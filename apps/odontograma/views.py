"""apps/odontograma/views.py"""
import json
import unicodedata

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.auditoria.models import Bitacora
from apps.core.mixins import LoginRequeridoMixin
from apps.core.permissions import puede_editar_clinico, puede_ver_clinico
from apps.fichas.models import EvolucionClinica, FichaClinica
from apps.odontograma.models import (
    CaraDental,
    CondicionOdontologica,
    HistorialOdontograma,
    Odontograma,
    OdontogramaDetalle,
    OdontogramaPeriodontal,
    OdontogramaPieza,
    OdontogramaRaiz,
    PiezaDental,
)
from apps.odontograma.services import obtener_info_pieza


CONDICION_ALIASES = {
    "obturacion": "restauracion",
    "restauracion": "restauracion",
    "restauracion_defectuosa": "restauracion",
    "extraccion": "extraccion_indicada",
    "extraccion_indicada": "extraccion_indicada",
    "extraccion indicada": "extraccion_indicada",
    "observacion": "observacion",
    "movilidad": "movilidad",
}


def _normalizar(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return (
        texto.strip()
        .lower()
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def _condicion_key(nombre):
    key = _normalizar(nombre)
    return CONDICION_ALIASES.get(key, key)


def _cara_key(nombre):
    key = _normalizar(nombre)
    aliases = {
        "palatino": "palatina",
        "palatina_lingual": "lingual",
        "lingual_palatina": "lingual",
        "oclusial": "oclusal",
    }
    return aliases.get(key, key)


def _cara_clinica_para_pieza(codigo_pieza, cara):
    cara = _cara_key(cara)
    info = obtener_info_pieza(codigo_pieza)
    caras_validas = set(info.get("caras_coronarias", []))
    if cara in caras_validas:
        return cara
    cuadrante = int(str(codigo_pieza)[0]) if str(codigo_pieza).isdigit() else 0
    pieza = int(str(codigo_pieza)[-1]) if str(codigo_pieza).isdigit() else 0
    es_superior = cuadrante in (1, 2, 5, 6)
    es_anterior = pieza in (1, 2, 3)
    if cara == "palatina" and not es_superior:
        return "lingual"
    if cara == "lingual" and es_superior:
        return "palatina"
    if cara == "oclusal" and es_anterior:
        return "incisal"
    if cara == "incisal" and not es_anterior:
        return "oclusal"
    return cara


def _odontologo_usuario(usuario):
    try:
        return usuario.odontologo
    except Exception:
        return None


def _es_supervision(usuario):
    return usuario.tiene_rol("administrador", "director", "director_clinico")


def _validar_acceso_odontograma(request, odontograma, edicion=False):
    if edicion:
        if not puede_editar_clinico(request.user):
            _auditar_acceso_denegado(request, odontograma)
            raise PermissionDenied("No tienes permisos para modificar odontogramas.")
    elif not puede_ver_clinico(request.user):
        _auditar_acceso_denegado(request, odontograma)
        raise PermissionDenied("No tienes permisos para ver odontogramas.")

    if _es_supervision(request.user):
        return

    if request.user.tiene_rol("odontologo"):
        odontologo = _odontologo_usuario(request.user)
        if not odontologo:
            raise PermissionDenied("Tu usuario no tiene perfil de odontologo asociado.")
        if odontograma.id_odontologo_id and odontograma.id_odontologo_id != odontologo.id_odontologo:
            raise PermissionDenied("No tienes permisos para este odontograma.")
        if not odontograma.id_odontologo_id:
            asignado = odontograma.paciente.citas.filter(id_odontologo=odontologo).exists()
            if not asignado:
                raise PermissionDenied("No tienes permisos para este paciente.")


def _auditar_acceso_denegado(request, odontograma=None):
    Bitacora.registrar(
        usuario=request.user,
        modulo="odontograma",
        accion="acceso_denegado",
        tabla_afectada="odontogramas",
        id_registro_afectado=getattr(odontograma, "id_odontograma", "-"),
        descripcion="Intento de acceso a odontograma sin permisos",
        request=request,
        paciente=getattr(odontograma, "paciente", None) if odontograma else None,
    )


def _resolver_contexto_clinico(request, ficha):
    evolucion = None
    odontologo = None
    cita = None

    evolucion_id = request.GET.get("evolucion")
    cita_id = request.GET.get("cita")

    if evolucion_id:
        evolucion = get_object_or_404(
            EvolucionClinica.objects.select_related("id_cita__id_odontologo", "id_odontologo"),
            pk=evolucion_id,
        )
        if evolucion.id_ficha_clinica_id and evolucion.id_ficha_clinica_id != ficha.id_ficha_clinica:
            raise PermissionDenied("La evolucion no pertenece a esta ficha clinica.")
        cita = evolucion.id_cita
        odontologo = evolucion.id_odontologo or evolucion.id_cita.id_odontologo
    elif cita_id:
        from apps.agenda.models import Cita

        cita = get_object_or_404(
            Cita.objects.select_related("id_paciente", "id_odontologo"),
            pk=cita_id,
        )
        if cita.id_paciente_id != ficha.id_paciente_id:
            raise PermissionDenied("La cita no pertenece al paciente de la ficha.")
        evolucion = getattr(cita, "evolucion", None)
        odontologo = cita.id_odontologo

    if not odontologo:
        odontologo = _odontologo_usuario(request.user)

    if request.user.tiene_rol("odontologo") and not _es_supervision(request.user):
        odontologo_actual = _odontologo_usuario(request.user)
        if not odontologo_actual:
            raise PermissionDenied("Tu usuario no tiene perfil de odontologo asociado.")
        if odontologo and odontologo.id_odontologo != odontologo_actual.id_odontologo:
            raise PermissionDenied("No puedes crear un odontograma para otro odontologo.")
        odontologo = odontologo_actual

    return evolucion, odontologo, cita


def _obtener_cara(codigo_pieza, valor, crear=False):
    if str(valor).isdigit():
        cara = CaraDental.objects.filter(pk=int(valor)).first()
        if cara:
            nombre = _cara_clinica_para_pieza(codigo_pieza, cara.nombre)
            if nombre != cara.nombre:
                return _obtener_cara(codigo_pieza, nombre, crear=crear)
            return cara
    nombre = _cara_clinica_para_pieza(codigo_pieza, valor)
    caras_validas = set(obtener_info_pieza(codigo_pieza).get("caras_coronarias", []))
    if nombre not in caras_validas:
        return None
    if crear:
        cara, _ = CaraDental.objects.get_or_create(nombre=nombre)
        return cara
    return CaraDental.objects.filter(nombre=nombre).first()


def _obtener_condicion(valor):
    if valor in (None, "", "0", 0, "sin_dato"):
        return None
    if str(valor).isdigit():
        return CondicionOdontologica.objects.filter(pk=int(valor), estado_condicion="activo").first()

    key = _condicion_key(valor)
    candidatos = [key]
    if key == "restauracion":
        candidatos.append("obturacion")
    if key == "extraccion_indicada":
        candidatos.append("extraccion")

    condiciones = list(CondicionOdontologica.objects.filter(estado_condicion="activo"))
    for candidato in candidatos:
        for condicion in condiciones:
            if _normalizar(condicion.nombre) == candidato:
                return condicion
    return None


def _estado_inicial(odontograma):
    estado = {}
    for det in odontograma.detalles.all():
        pieza = str(det.codigo_pieza_dental_id)
        estado.setdefault(pieza, {})[det.id_cara_dental.nombre] = _condicion_key(det.id_condicion.nombre)
    for pieza in odontograma.piezas.all():
        key = str(pieza.codigo_pieza_dental_id)
        estado.setdefault(key, {})["_estado"] = pieza.estado_general
    return estado


def _registrar_historial(
    odontograma,
    pieza_dental,
    usuario,
    tipo_cambio,
    detalle_cambio,
    estado_anterior=None,
    estado_nuevo=None,
):
    evolucion = odontograma.id_evolucion
    cita = evolucion.id_cita if evolucion else None
    HistorialOdontograma.objects.create(
        odontograma=odontograma,
        pieza_dental=pieza_dental,
        evolucion=evolucion,
        cita=cita,
        usuario=usuario,
        tipo_cambio=tipo_cambio,
        detalle_cambio=detalle_cambio,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
    )


def _marcar_actualizado(odontograma, usuario):
    campos = ["id_usuario_actualiza"]
    odontograma.id_usuario_actualiza = usuario
    if not odontograma.id_odontologo_id:
        odontologo = _odontologo_usuario(usuario)
        if odontologo:
            odontograma.id_odontologo = odontologo
            campos.append("id_odontologo")
    odontograma.save(update_fields=campos + ["fecha_actualizacion"])


def _json_error(mensaje, status=400):
    return JsonResponse({"success": False, "error": mensaje}, status=status)


def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValidationError("Solicitud JSON invalida.")


class OdontogramaCrearView(LoginRequeridoMixin, View):
    def get(self, request, ficha_id):
        if not puede_editar_clinico(request.user):
            raise PermissionDenied("No tienes permisos para crear odontogramas.")

        ficha = get_object_or_404(FichaClinica.objects.select_related("id_paciente"), pk=ficha_id)
        evolucion, odontologo, cita = _resolver_contexto_clinico(request, ficha)

        if evolucion:
            existente = Odontograma.objects.filter(
                id_evolucion=evolucion,
                estado_odontograma=Odontograma.ESTADO_ACTIVO,
            ).order_by("-version").first()
            if existente:
                messages.info(request, "La evolucion ya tiene un odontograma asociado.")
                return redirect("odontograma:detalle", pk=existente.id_odontograma)

        with transaction.atomic():
            ultima_version = (
                Odontograma.objects.filter(id_ficha_clinica=ficha)
                .aggregate(max_version=Max("version"))
                .get("max_version")
                or 0
            )
            odontograma = Odontograma.objects.create(
                id_ficha_clinica=ficha,
                id_evolucion=evolucion,
                id_odontologo=odontologo,
                id_usuario_crea=request.user,
                id_usuario_actualiza=request.user,
                version=ultima_version + 1,
                descripcion_general="Odontograma clinico inicial",
            )

        Bitacora.registrar(
            usuario=request.user,
            modulo="odontograma",
            accion="creacion",
            tabla_afectada="odontogramas",
            id_registro_afectado=odontograma.id_odontograma,
            descripcion=f"Odontograma v{odontograma.version} creado",
            request=request,
            paciente=ficha.id_paciente,
            cita=cita,
            objeto_afectado=f"Odontograma #{odontograma.id_odontograma}",
        )
        messages.success(request, f"Odontograma version {odontograma.version} inicializado.")
        return redirect("odontograma:detalle", pk=odontograma.id_odontograma)


class OdontogramaDetalleView(LoginRequeridoMixin, View):
    template_name = "odontograma/detalle.html"

    def get(self, request, pk):
        odontograma = get_object_or_404(
            Odontograma.objects.select_related(
                "id_ficha_clinica__id_paciente__id_persona",
                "id_evolucion__id_cita",
                "id_odontologo__id_usuario__id_persona",
                "id_usuario_crea__id_persona",
                "id_usuario_actualiza__id_persona",
            ).prefetch_related(
                "detalles__codigo_pieza_dental",
                "detalles__id_cara_dental",
                "detalles__id_condicion",
                "piezas__codigo_pieza_dental",
                "piezas__raices__id_condicion",
                "piezas__periodonto",
            ),
            pk=pk,
        )
        _validar_acceso_odontograma(request, odontograma, edicion=False)
        puede_editar = puede_editar_clinico(request.user)
        if puede_editar:
            try:
                _validar_acceso_odontograma(request, odontograma, edicion=True)
            except PermissionDenied:
                puede_editar = False

        condiciones = CondicionOdontologica.objects.filter(
            estado_condicion="activo"
        ).order_by("nombre")
        return render(request, self.template_name, {
            "odontograma": odontograma,
            "condiciones": condiciones,
            "estado_inicial": _estado_inicial(odontograma),
            "puede_editar": puede_editar,
        })


class OdontogramaDetalleGuardarView(LoginRequeridoMixin, View):
    """Endpoint compatible con el formulario clasico."""

    def post(self, request, pk):
        odontograma = get_object_or_404(Odontograma, pk=pk)
        _validar_acceso_odontograma(request, odontograma, edicion=True)
        actualizados = 0
        creados = 0
        eliminados = 0
        errores = []

        with transaction.atomic():
            for key, condicion_valor in request.POST.items():
                if not key.startswith("cond_"):
                    continue
                try:
                    _, pieza_cod, cara_token = key.split("_", 2)
                    pieza = PiezaDental.objects.get(pk=pieza_cod)
                    cara = _obtener_cara(pieza_cod, cara_token, crear=True)
                    if not cara:
                        errores.append(f"Cara invalida para pieza {pieza_cod}: {cara_token}")
                        continue

                    condicion = _obtener_condicion(condicion_valor)
                    observacion = request.POST.get(f"obs_{pieza_cod}_{cara_token}", "").strip() or None
                    existente = OdontogramaDetalle.objects.filter(
                        id_odontograma=odontograma,
                        codigo_pieza_dental=pieza,
                        id_cara_dental=cara,
                    ).select_related("id_condicion").first()

                    if not condicion:
                        if existente:
                            anterior = existente.id_condicion.nombre
                            existente.delete()
                            eliminados += 1
                            _registrar_historial(
                                odontograma,
                                pieza,
                                request.user,
                                "superficie",
                                f"Elimino condicion en cara {cara.nombre}",
                                estado_anterior=anterior,
                                estado_nuevo="sin_dato",
                            )
                        continue

                    detalle, created = OdontogramaDetalle.objects.update_or_create(
                        id_odontograma=odontograma,
                        codigo_pieza_dental=pieza,
                        id_cara_dental=cara,
                        defaults={"id_condicion": condicion, "observacion": observacion},
                    )
                    if created:
                        creados += 1
                        anterior = "sin_dato"
                    else:
                        actualizados += 1
                        anterior = existente.id_condicion.nombre if existente else "sin_dato"
                    _registrar_historial(
                        odontograma,
                        pieza,
                        request.user,
                        "superficie",
                        f"Cara {cara.nombre}: {anterior} -> {condicion.nombre}",
                        estado_anterior=anterior,
                        estado_nuevo=condicion.nombre,
                    )
                except Exception as exc:
                    errores.append(str(exc))

            _marcar_actualizado(odontograma, request.user)

        Bitacora.registrar(
            usuario=request.user,
            modulo="odontograma",
            accion="edicion",
            tabla_afectada="odontograma_detalle",
            id_registro_afectado=odontograma.id_odontograma,
            descripcion=f"Odontograma #{odontograma.id_odontograma}: {creados} nuevos, {actualizados} actualizados, {eliminados} eliminados",
            request=request,
            paciente=odontograma.paciente,
        )
        if errores:
            messages.warning(request, "Odontograma guardado con algunas advertencias.")
        else:
            messages.success(request, "Odontograma actualizado correctamente.")
        return redirect("odontograma:detalle", pk=pk)


class OdontogramaPiezaAPIView(LoginRequeridoMixin, View):
    """Obtiene el estado completo de una pieza sin crear registros al visualizar."""

    def get(self, request, odontograma_id, codigo_pieza):
        odontograma = get_object_or_404(Odontograma, pk=odontograma_id)
        _validar_acceso_odontograma(request, odontograma, edicion=False)
        pieza_dental = get_object_or_404(PiezaDental, pk=codigo_pieza)
        pieza_obj = (
            OdontogramaPieza.objects.filter(
                odontograma=odontograma,
                codigo_pieza_dental=pieza_dental,
            )
            .select_related("codigo_pieza_dental")
            .first()
        )

        detalles_superficie = OdontogramaDetalle.objects.filter(
            id_odontograma=odontograma,
            codigo_pieza_dental=pieza_dental,
        ).select_related("id_cara_dental", "id_condicion")

        superficies = [
            {
                "cara": det.id_cara_dental.nombre,
                "cara_key": _cara_key(det.id_cara_dental.nombre),
                "condicion": det.id_condicion.nombre,
                "condicion_key": _condicion_key(det.id_condicion.nombre),
                "observacion": det.observacion or "",
            }
            for det in detalles_superficie
        ]

        raices = []
        periodonto = {}
        if pieza_obj:
            for raiz in pieza_obj.raices.select_related("id_condicion").all():
                condicion = raiz.id_condicion.nombre if raiz.id_condicion else ""
                raices.append({
                    "id": raiz.id,
                    "raiz": raiz.raiz,
                    "tercio": raiz.tercio,
                    "condicion": condicion,
                    "condicion_key": _condicion_key(condicion),
                    "observacion": raiz.observacion or "",
                })
            try:
                perio = pieza_obj.periodonto
                periodonto = {
                    "movilidad": perio.movilidad or "",
                    "profundidad_sondaje": perio.profundidad_sondaje or "",
                    "recesion": perio.recesion or "",
                    "sangrado": perio.sangrado,
                    "placa": perio.placa,
                    "supuracion": perio.supuracion,
                    "furca": perio.furca or "",
                    "observacion": perio.observacion or "",
                }
            except OdontogramaPeriodontal.DoesNotExist:
                periodonto = {}

        historial_db = HistorialOdontograma.objects.filter(
            odontograma=odontograma,
            pieza_dental=pieza_dental,
        ).select_related("usuario__id_persona").order_by("-fecha")[:10]

        historial = []
        for item in historial_db:
            nombre_usuario = item.usuario.nombre_completo if item.usuario else "Sistema"
            historial.append({
                "tipo_cambio": item.tipo_cambio,
                "detalle_cambio": item.detalle_cambio,
                "estado_anterior": item.estado_anterior or "",
                "estado_nuevo": item.estado_nuevo or "",
                "usuario": nombre_usuario,
                "fecha": item.fecha.strftime("%d/%m/%Y %H:%M"),
            })

        return JsonResponse({
            "success": True,
            "anatomia": obtener_info_pieza(codigo_pieza),
            "estado_general": pieza_obj.estado_general if pieza_obj else "presente",
            "observacion_pieza": pieza_obj.observacion if pieza_obj and pieza_obj.observacion else "",
            "superficies": superficies,
            "raices": raices,
            "periodonto": periodonto,
            "historial": historial,
            "puede_editar": puede_editar_clinico(request.user),
        })


class OdontogramaActualizarEstadoAPIView(LoginRequeridoMixin, View):
    def post(self, request, odontograma_id, codigo_pieza):
        odontograma = get_object_or_404(Odontograma, pk=odontograma_id)
        _validar_acceso_odontograma(request, odontograma, edicion=True)
        try:
            data = _json_body(request)
            pieza_dental = get_object_or_404(PiezaDental, pk=codigo_pieza)
            estados_validos = dict(OdontogramaPieza.ESTADO_GENERAL_CHOICES)
            nuevo_estado = data.get("estado_general", "presente")
            observacion = (data.get("observacion") or "").strip()
            if nuevo_estado not in estados_validos:
                return _json_error("Estado general invalido.")

            with transaction.atomic():
                pieza_obj, _ = OdontogramaPieza.objects.get_or_create(
                    odontograma=odontograma,
                    codigo_pieza_dental=pieza_dental,
                )
                estado_anterior = pieza_obj.estado_general
                observacion_anterior = pieza_obj.observacion or ""
                if estado_anterior != nuevo_estado or observacion_anterior != observacion:
                    pieza_obj.estado_general = nuevo_estado
                    pieza_obj.observacion = observacion
                    pieza_obj.save()
                    _registrar_historial(
                        odontograma,
                        pieza_dental,
                        request.user,
                        "estado_general",
                        f"Estado general: {estado_anterior} -> {nuevo_estado}",
                        estado_anterior=estado_anterior,
                        estado_nuevo=nuevo_estado,
                    )
                    _marcar_actualizado(odontograma, request.user)
            return JsonResponse({"success": True, "message": "Estado actualizado"})
        except ValidationError as exc:
            return _json_error(str(exc))


class OdontogramaActualizarSuperficieAPIView(LoginRequeridoMixin, View):
    def post(self, request, odontograma_id, codigo_pieza):
        odontograma = get_object_or_404(Odontograma, pk=odontograma_id)
        _validar_acceso_odontograma(request, odontograma, edicion=True)
        try:
            data = _json_body(request)
            pieza_dental = get_object_or_404(PiezaDental, pk=codigo_pieza)
            cara = _obtener_cara(codigo_pieza, data.get("cara"), crear=True)
            if not cara:
                return _json_error("Cara dental invalida.")
            condicion = _obtener_condicion(data.get("condicion"))
            observacion = (data.get("observacion") or "").strip() or None

            with transaction.atomic():
                existente = OdontogramaDetalle.objects.filter(
                    id_odontograma=odontograma,
                    codigo_pieza_dental=pieza_dental,
                    id_cara_dental=cara,
                ).select_related("id_condicion").first()

                if not condicion:
                    if existente:
                        anterior = existente.id_condicion.nombre
                        existente.delete()
                        _registrar_historial(
                            odontograma,
                            pieza_dental,
                            request.user,
                            "superficie",
                            f"Elimino condicion en cara {cara.nombre}",
                            estado_anterior=anterior,
                            estado_nuevo="sin_dato",
                        )
                        _marcar_actualizado(odontograma, request.user)
                    return JsonResponse({"success": True, "message": "Superficie eliminada"})

                anterior = existente.id_condicion.nombre if existente else "sin_dato"
                detalle, created = OdontogramaDetalle.objects.update_or_create(
                    id_odontograma=odontograma,
                    codigo_pieza_dental=pieza_dental,
                    id_cara_dental=cara,
                    defaults={"id_condicion": condicion, "observacion": observacion},
                )
                detalle.clean()
                if created or anterior != condicion.nombre or (existente and existente.observacion != observacion):
                    _registrar_historial(
                        odontograma,
                        pieza_dental,
                        request.user,
                        "superficie",
                        f"Cara {cara.nombre}: {anterior} -> {condicion.nombre}",
                        estado_anterior=anterior,
                        estado_nuevo=condicion.nombre,
                    )
                    _marcar_actualizado(odontograma, request.user)
            return JsonResponse({"success": True, "message": "Superficie actualizada"})
        except ValidationError as exc:
            return _json_error(str(exc))


class OdontogramaActualizarRaizAPIView(LoginRequeridoMixin, View):
    def post(self, request, odontograma_id, codigo_pieza):
        odontograma = get_object_or_404(Odontograma, pk=odontograma_id)
        _validar_acceso_odontograma(request, odontograma, edicion=True)
        try:
            data = _json_body(request)
            pieza_dental = get_object_or_404(PiezaDental, pk=codigo_pieza)
            raiz = _normalizar(data.get("raiz"))
            tercio = _normalizar(data.get("tercio") or "completo")
            raiz_choices = dict(OdontogramaRaiz.RAIZ_CHOICES)
            tercio_choices = dict(OdontogramaRaiz.TERCIO_CHOICES)
            if raiz not in raiz_choices:
                return _json_error("Raiz invalida.")
            if tercio not in tercio_choices:
                return _json_error("Tercio radicular invalido.")

            condicion = _obtener_condicion(data.get("condicion"))
            observacion = (data.get("observacion") or "").strip() or None

            with transaction.atomic():
                pieza_obj, _ = OdontogramaPieza.objects.get_or_create(
                    odontograma=odontograma,
                    codigo_pieza_dental=pieza_dental,
                )
                existente = OdontogramaRaiz.objects.filter(
                    pieza=pieza_obj,
                    raiz=raiz,
                    tercio=tercio,
                ).select_related("id_condicion").first()

                if not condicion:
                    if existente:
                        anterior = existente.id_condicion.nombre if existente.id_condicion else "sin_dato"
                        existente.delete()
                        _registrar_historial(
                            odontograma,
                            pieza_dental,
                            request.user,
                            "raiz",
                            f"Elimino condicion en raiz {raiz} ({tercio})",
                            estado_anterior=anterior,
                            estado_nuevo="sin_dato",
                        )
                        _marcar_actualizado(odontograma, request.user)
                    return JsonResponse({"success": True, "message": "Raiz eliminada"})

                anterior = existente.id_condicion.nombre if existente and existente.id_condicion else "sin_dato"
                obj, created = OdontogramaRaiz.objects.update_or_create(
                    pieza=pieza_obj,
                    raiz=raiz,
                    tercio=tercio,
                    defaults={"id_condicion": condicion, "observacion": observacion},
                )
                if created or anterior != condicion.nombre or (existente and existente.observacion != observacion):
                    _registrar_historial(
                        odontograma,
                        pieza_dental,
                        request.user,
                        "raiz",
                        f"Raiz {raiz} ({tercio}): {anterior} -> {condicion.nombre}",
                        estado_anterior=anterior,
                        estado_nuevo=condicion.nombre,
                    )
                    _marcar_actualizado(odontograma, request.user)
            return JsonResponse({"success": True, "message": "Raiz actualizada"})
        except ValidationError as exc:
            return _json_error(str(exc))


class OdontogramaDescripcionAPIView(LoginRequeridoMixin, View):
    def post(self, request, odontograma_id):
        odontograma = get_object_or_404(Odontograma, pk=odontograma_id)
        _validar_acceso_odontograma(request, odontograma, edicion=True)
        try:
            data = _json_body(request)
            desc = (data.get("descripcion_general") or "").strip()
            anterior = odontograma.descripcion_general or ""
            odontograma.descripcion_general = desc
            odontograma.id_usuario_actualiza = request.user
            odontograma.save(update_fields=[
                "descripcion_general",
                "id_usuario_actualiza",
                "fecha_actualizacion",
            ])
            Bitacora.registrar(
                usuario=request.user,
                modulo="odontograma",
                accion="modificacion",
                tabla_afectada="odontogramas",
                id_registro_afectado=odontograma.id_odontograma,
                descripcion=f"Descripcion general actualizada (v{odontograma.version})",
                request=request,
                paciente=odontograma.paciente,
                datos_anteriores={"descripcion_general": anterior},
                datos_nuevos={"descripcion_general": desc},
            )
            return JsonResponse({"success": True, "message": "Descripcion guardada"})
        except ValidationError as exc:
            return _json_error(str(exc))


class OdontogramaActualizarPeriodontoAPIView(LoginRequeridoMixin, View):
    def post(self, request, odontograma_id, codigo_pieza):
        odontograma = get_object_or_404(Odontograma, pk=odontograma_id)
        _validar_acceso_odontograma(request, odontograma, edicion=True)
        try:
            data = _json_body(request)
            pieza_dental = get_object_or_404(PiezaDental, pk=codigo_pieza)
            campos = {
                "movilidad": (data.get("movilidad") or "").strip() or None,
                "furca": (data.get("furca") or "").strip() or None,
                "profundidad_sondaje": (data.get("profundidad_sondaje") or "").strip() or None,
                "recesion": (data.get("recesion") or "").strip() or None,
                "observacion": (data.get("observacion") or "").strip() or None,
                "sangrado": bool(data.get("sangrado")),
                "placa": bool(data.get("placa")),
                "supuracion": bool(data.get("supuracion")),
            }

            with transaction.atomic():
                pieza_obj, _ = OdontogramaPieza.objects.get_or_create(
                    odontograma=odontograma,
                    codigo_pieza_dental=pieza_dental,
                )
                perio, _ = OdontogramaPeriodontal.objects.get_or_create(pieza=pieza_obj)
                anterior = {
                    campo: getattr(perio, campo)
                    for campo in campos
                }
                for campo, valor in campos.items():
                    setattr(perio, campo, valor)
                perio.save()
                if anterior != campos:
                    _registrar_historial(
                        odontograma,
                        pieza_dental,
                        request.user,
                        "periodonto",
                        "Actualizo datos periodontales",
                        estado_anterior=json.dumps(anterior, ensure_ascii=False),
                        estado_nuevo=json.dumps(campos, ensure_ascii=False),
                    )
                    _marcar_actualizado(odontograma, request.user)
            return JsonResponse({"success": True, "message": "Periodonto actualizado"})
        except ValidationError as exc:
            return _json_error(str(exc))
