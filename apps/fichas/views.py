"""
apps/fichas/views.py
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from apps.core.mixins import LoginRequeridoMixin
from apps.core.permissions import puede_atender_cita, puede_editar_clinico
from apps.fichas.models import FichaClinica, EvolucionClinica, AdjuntoClinico
from apps.agenda.models import Cita
from apps.pacientes.models import Paciente
from apps.auditoria.models import Bitacora


def _asegurar_ficha(paciente):
    ficha = FichaClinica.objects.filter(id_paciente=paciente).first()
    if ficha:
        return ficha, False
    import uuid
    ficha = FichaClinica.objects.create(
        id_paciente=paciente,
        numero_ficha=f"FC-{str(uuid.uuid4()).upper()[:8]}",
        fecha_apertura=timezone.localdate(),
        estado_ficha=FichaClinica.ESTADO_ACTIVA,
    )
    return ficha, True


def _datos_evolucion_desde_post(request):
    return {
        "motivo_consulta": request.POST.get("motivo_consulta", "").strip(),
        "anamnesis": request.POST.get("anamnesis", "").strip(),
        "diagnostico": request.POST.get("diagnostico", "").strip(),
        "procedimiento_realizado": request.POST.get("procedimiento_realizado", "").strip(),
        "indicaciones": request.POST.get("indicaciones", "").strip(),
        "observaciones": request.POST.get("observaciones", "").strip(),
        "tratamiento_sugerido": request.POST.get("tratamiento_sugerido", "").strip(),
        "proxima_accion": request.POST.get("proxima_accion", "").strip(),
    }


def _estado_cita_por_nombre(*nombres):
    from apps.agenda.models import EstadoCita
    for nombre in nombres:
        estado = EstadoCita.objects.filter(nombre=nombre).first()
        if estado:
            return estado
    return None


class FichaDetalleView(LoginRequeridoMixin, View):
    template_name = "fichas/detalle.html"

    def get(self, request, paciente_id):
        paciente = get_object_or_404(
            Paciente.objects.select_related("id_persona"), pk=paciente_id
        )
        ficha = FichaClinica.objects.filter(id_paciente=paciente).first()
        evoluciones = []
        odontogramas = []
        if ficha:
            evoluciones = (
                EvolucionClinica.objects.filter(id_cita__id_paciente=paciente)
                .select_related("id_cita__id_odontologo__id_usuario__id_persona")
                .prefetch_related("adjuntos")
                .order_by("-fecha_evolucion")
            )
            from apps.odontograma.models import Odontograma
            odontogramas = Odontograma.objects.filter(id_ficha_clinica=ficha).order_by("-version")
        return render(request, self.template_name, {
            "paciente": paciente,
            "ficha": ficha,
            "evoluciones": evoluciones,
            "odontogramas": odontogramas,
            "tiene_ficha": ficha is not None,
        })


class AbrirFichaView(LoginRequeridoMixin, View):
    def post(self, request, paciente_id):
        if not puede_editar_clinico(request.user):
            raise PermissionDenied("No tienes permisos para editar informacion clinica.")
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        if FichaClinica.objects.filter(id_paciente=paciente).exists():
            messages.info(request, "Este paciente ya tiene ficha clínica.")
            return redirect("fichas:detalle", paciente_id=paciente_id)
        with transaction.atomic():
            import uuid
            numero = f"FC-{str(uuid.uuid4()).upper()[:8]}"
            ficha = FichaClinica.objects.create(
                id_paciente=paciente,
                numero_ficha=numero,
                fecha_apertura=timezone.localdate(),
                estado_ficha="activa",
            )
        Bitacora.registrar(
            usuario=request.user,
            modulo="fichas",
            accion="creacion",
            tabla_afectada="fichas_clinicas",
            id_registro_afectado=ficha.id_ficha_clinica,
            descripcion=f"Ficha {numero} abierta para {paciente.nombre_completo}",
            ip_origen=getattr(request, "ip_origen", None),
            paciente=paciente,
        )
        messages.success(request, f"Ficha clínica {numero} abierta correctamente.")
        return redirect("fichas:detalle", paciente_id=paciente_id)


class FichaEditarView(LoginRequeridoMixin, View):
    """Editar observaciones clínicas generales de la ficha."""

    def post(self, request, paciente_id):
        if not puede_editar_clinico(request.user):
            raise PermissionDenied("No tienes permisos para editar informacion clinica.")
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        ficha = get_object_or_404(FichaClinica, id_paciente=paciente)
        ficha.observaciones_clinicas_generales = request.POST.get("observaciones_clinicas_generales", "")
        ficha.save(update_fields=["observaciones_clinicas_generales"])
        Bitacora.registrar(
            usuario=request.user,
            modulo="fichas",
            accion="edicion",
            tabla_afectada="fichas_clinicas",
            id_registro_afectado=ficha.id_ficha_clinica,
            descripcion=f"Ficha {ficha.numero_ficha} — observaciones editadas",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, "Observaciones de la ficha actualizadas.")
        return redirect("fichas:detalle", paciente_id=paciente_id)


class FichaCambiarEstadoView(LoginRequeridoMixin, View):
    """Cambiar estado de ficha (activa / cerrada / bloqueada)."""

    TRANSICIONES_VALIDAS = {
        "activa": ["cerrada", "bloqueada"],
        "cerrada": ["activa"],
        "bloqueada": ["activa"],
    }

    def post(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        ficha = get_object_or_404(FichaClinica, id_paciente=paciente)
        nuevo_estado = request.POST.get("estado", "").strip()

        estados_validos = dict(FichaClinica.ESTADO_CHOICES)
        if nuevo_estado not in estados_validos:
            messages.error(request, "Estado inválido.")
            return redirect("fichas:detalle", paciente_id=paciente_id)

        transiciones = self.TRANSICIONES_VALIDAS.get(ficha.estado_ficha, [])
        if nuevo_estado not in transiciones:
            messages.error(
                request,
                f"No se puede pasar de '{ficha.estado_ficha}' a '{nuevo_estado}'."
            )
            return redirect("fichas:detalle", paciente_id=paciente_id)

        estado_anterior = ficha.estado_ficha
        ficha.estado_ficha = nuevo_estado
        ficha.save(update_fields=["estado_ficha"])
        Bitacora.registrar(
            usuario=request.user,
            modulo="fichas",
            accion="cambio_estado",
            tabla_afectada="fichas_clinicas",
            id_registro_afectado=ficha.id_ficha_clinica,
            descripcion=f"Ficha {ficha.numero_ficha}: {estado_anterior} → {nuevo_estado}",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, f"Estado de la ficha cambiado a '{nuevo_estado}'.")
        return redirect("fichas:detalle", paciente_id=paciente_id)


class AtencionCitaView(LoginRequeridoMixin, View):
    """Modo Atencion: flujo clinico unico para odontologo y supervision."""
    template_name = "fichas/atencion.html"

    def _obtener_cita(self, cita_id):
        return get_object_or_404(
            Cita.objects.select_related(
                "id_paciente__id_persona",
                "id_odontologo__id_usuario__id_persona",
                "id_estado_cita",
                "id_box",
                "id_tipo_atencion",
            ),
            pk=cita_id,
        )

    def _validar_acceso(self, request, cita):
        if not puede_atender_cita(request.user, cita):
            Bitacora.registrar(
                usuario=request.user,
                modulo="fichas",
                accion="acceso_denegado",
                tabla_afectada="citas",
                id_registro_afectado=cita.id_cita,
                descripcion=f"Acceso denegado a modo atencion cita #{cita.id_cita}",
                request=request,
                paciente=cita.id_paciente,
                cita=cita,
            )
            raise PermissionDenied("No tienes permisos para atender esta cita.")

    def _contexto(self, cita, ficha, evolucion):
        from apps.antecedentes.models import RegistroAntecedentesMedicos
        from apps.imagenologia.models import ExamenImagenologico
        from apps.odontograma.models import Odontograma
        from apps.tratamientos.models import PlanTratamiento
        from apps.presupuestos.models import Presupuesto
        from apps.pagos.models import Pago

        antecedentes = (
            RegistroAntecedentesMedicos.objects.filter(id_paciente=cita.id_paciente)
            .prefetch_related("detalles__id_catalogo_antecedente")
            .order_by("-fecha_registro")
        )
        odontogramas = (
            Odontograma.objects.filter(id_ficha_clinica=ficha)
            .prefetch_related("detalles__id_condicion", "piezas")
            .order_by("-version")
        )
        imagenes = (
            ExamenImagenologico.objects.filter(paciente=cita.id_paciente)
            .select_related("tipo_examen", "creado_por__id_persona")
            .prefetch_related("archivos")
            .order_by("-fecha_examen", "-id_examen")
        )
        planes = (
            PlanTratamiento.objects.filter(id_ficha_clinica=ficha)
            .select_related("id_odontologo__id_usuario__id_persona")
            .prefetch_related("detalles__id_tratamiento", "presupuestos")
            .order_by("-fecha_creacion")
        )
        presupuestos = (
            Presupuesto.objects.filter(id_plan_tratamiento__id_ficha_clinica=ficha)
            .prefetch_related("detalles", "pagos")
            .order_by("-fecha_emision")
        )
        pagos = (
            Pago.objects.filter(id_presupuesto__id_plan_tratamiento__id_ficha_clinica=ficha)
            .select_related("id_medio_pago", "id_presupuesto")
            .order_by("-fecha_pago")
        )
        return {
            "cita": cita,
            "paciente": cita.id_paciente,
            "ficha": ficha,
            "evolucion": evolucion,
            "antecedentes": antecedentes,
            "odontogramas": odontogramas,
            "odontograma_actual": odontogramas.first(),
            "imagenes": imagenes,
            "planes": planes,
            "presupuestos": presupuestos,
            "pagos": pagos,
        }

    def get(self, request, cita_id):
        cita = self._obtener_cita(cita_id)
        self._validar_acceso(request, cita)

        with transaction.atomic():
            ficha, ficha_creada = _asegurar_ficha(cita.id_paciente)
            if ficha_creada:
                Bitacora.registrar(
                    usuario=request.user,
                    modulo="fichas",
                    accion="creacion",
                    tabla_afectada="fichas_clinicas",
                    id_registro_afectado=ficha.id_ficha_clinica,
                    descripcion=f"Ficha {ficha.numero_ficha} abierta desde modo atencion",
                    request=request,
                    paciente=cita.id_paciente,
                    cita=cita,
                )

            estado_en_atencion = _estado_cita_por_nombre("en_atencion")
            estados_finales = {"atendida", "cancelada", "reprogramada"}
            if (
                estado_en_atencion
                and cita.id_estado_cita.nombre not in estados_finales
                and cita.id_estado_cita != estado_en_atencion
            ):
                from apps.agenda.services import CitaService
                try:
                    CitaService.cambiar_estado(
                        cita=cita,
                        nuevo_estado=estado_en_atencion,
                        usuario=request.user,
                        motivo="Atencion clinica iniciada",
                    )
                    cita.refresh_from_db()
                except ValidationError:
                    pass

        evolucion = EvolucionClinica.objects.filter(id_cita=cita).first()
        Bitacora.registrar(
            usuario=request.user,
            modulo="fichas",
            accion="inicio_atencion",
            tabla_afectada="citas",
            id_registro_afectado=cita.id_cita,
            descripcion=f"Modo atencion abierto para cita #{cita.id_cita}",
            request=request,
            paciente=cita.id_paciente,
            cita=cita,
        )
        return render(request, self.template_name, self._contexto(cita, ficha, evolucion))

    def post(self, request, cita_id):
        cita = self._obtener_cita(cita_id)
        self._validar_acceso(request, cita)
        ficha, _ = _asegurar_ficha(cita.id_paciente)
        accion = request.POST.get("accion", "guardar_evolucion")

        if accion == "finalizar":
            evolucion = EvolucionClinica.objects.filter(id_cita=cita).first()
            if not evolucion or not evolucion.tiene_registro_minimo:
                messages.warning(
                    request,
                    "Debe registrar una evolucion antes de finalizar la atencion."
                )
                return redirect("fichas:modo_atencion", cita_id=cita.id_cita)
            estado_final = _estado_cita_por_nombre("atendida", "finalizada", "finalizado")
            if not estado_final:
                messages.error(request, "No existe un estado final de cita configurado.")
                return redirect("fichas:modo_atencion", cita_id=cita.id_cita)
            if cita.id_estado_cita != estado_final:
                from apps.agenda.services import CitaService
                CitaService.cambiar_estado(
                    cita=cita,
                    nuevo_estado=estado_final,
                    usuario=request.user,
                    motivo="Atencion clinica finalizada",
                )
            Bitacora.registrar(
                usuario=request.user,
                modulo="fichas",
                accion="finalizacion_atencion",
                tabla_afectada="citas",
                id_registro_afectado=cita.id_cita,
                descripcion=f"Atencion finalizada para cita #{cita.id_cita}",
                request=request,
                paciente=cita.id_paciente,
                cita=cita,
                objeto_afectado=f"Evolucion #{evolucion.id_evolucion}",
            )
            messages.success(request, "Atencion finalizada correctamente.")
            return redirect("pacientes:detalle", pk=cita.id_paciente_id)

        if not cita.id_odontologo_id:
            messages.error(request, "La evolucion requiere un odontologo responsable.")
            return redirect("fichas:modo_atencion", cita_id=cita.id_cita)

        datos = _datos_evolucion_desde_post(request)
        if not any(datos.values()):
            messages.warning(request, "Registra al menos un dato clinico de la evolucion.")
            return redirect("fichas:modo_atencion", cita_id=cita.id_cita)

        with transaction.atomic():
            evolucion, created = EvolucionClinica.objects.get_or_create(
                id_cita=cita,
                defaults={
                    "id_ficha_clinica": ficha,
                    "id_odontologo": cita.id_odontologo,
                },
            )
            datos_anteriores = {campo: getattr(evolucion, campo, None) for campo in datos}
            for campo, valor in datos.items():
                setattr(evolucion, campo, valor)
            evolucion.id_ficha_clinica = ficha
            evolucion.id_odontologo = cita.id_odontologo
            evolucion.save()

        Bitacora.registrar(
            usuario=request.user,
            modulo="fichas",
            accion="creacion" if created else "edicion",
            tabla_afectada="evoluciones_clinicas",
            id_registro_afectado=evolucion.id_evolucion,
            descripcion=f"Evolucion #{evolucion.id_evolucion} {'creada' if created else 'actualizada'} desde modo atencion",
            request=request,
            paciente=cita.id_paciente,
            cita=cita,
            datos_anteriores=datos_anteriores if not created else None,
            datos_nuevos=datos,
        )
        messages.success(request, "Evolucion clinica guardada correctamente.")
        return redirect("fichas:modo_atencion", cita_id=cita.id_cita)


class EvolucionCrearView(LoginRequeridoMixin, View):
    template_name = "fichas/evolucion_form.html"

    def get(self, request, cita_id):
        cita = get_object_or_404(
            Cita.objects.select_related(
                "id_paciente__id_persona",
                "id_odontologo__id_usuario__id_persona",
                "id_box",
            ),
            pk=cita_id,
        )
        if hasattr(cita, "evolucion"):
            messages.info(request, "Esta cita ya tiene una evolución registrada.")
            return redirect("fichas:evolucion_detalle", pk=cita.evolucion.id_evolucion)
        if not puede_atender_cita(request.user, cita):
            raise PermissionDenied("No tienes permisos para registrar esta evolucion.")
        return render(request, self.template_name, {
            "cita": cita,
            "editar": False,
        })

    def post(self, request, cita_id):
        cita = get_object_or_404(
            Cita.objects.select_related("id_paciente", "id_odontologo"),
            pk=cita_id,
        )
        if not puede_atender_cita(request.user, cita):
            raise PermissionDenied("No tienes permisos para registrar esta evolucion.")
        ficha, _ = _asegurar_ficha(cita.id_paciente)
        datos = _datos_evolucion_desde_post(request)
        if not any(datos.values()):
            messages.warning(request, "Registra al menos un dato clinico de la evolucion.")
            return redirect("fichas:evolucion_crear", cita_id=cita_id)
        with transaction.atomic():
            evolucion = EvolucionClinica.objects.create(
                id_cita=cita,
                id_ficha_clinica=ficha,
                id_odontologo=cita.id_odontologo,
                **datos,
            )
            # Marcar cita como atendida usando CitaService para registrar historial
            from apps.agenda.models import EstadoCita
            from apps.agenda.services import CitaService
            estado_atendida = EstadoCita.objects.filter(nombre="atendida").first()
            if estado_atendida and cita.id_estado_cita != estado_atendida:
                try:
                    CitaService.cambiar_estado(
                        cita=cita,
                        nuevo_estado=estado_atendida,
                        usuario=request.user,
                        motivo="Evolución clínica registrada",
                    )
                except ValidationError:
                    pass  # Ya estaba atendida o estado no cambió

        Bitacora.registrar(
            usuario=request.user,
            modulo="fichas",
            accion="creacion",
            tabla_afectada="evoluciones_clinicas",
            id_registro_afectado=evolucion.id_evolucion,
            descripcion=f"Evolución clínica #{evolucion.id_evolucion} creada",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, "Evolución clínica registrada correctamente.")
        return redirect("fichas:evolucion_detalle", pk=evolucion.id_evolucion)


class EvolucionDetalleView(LoginRequeridoMixin, View):
    template_name = "fichas/evolucion_detalle.html"

    def get(self, request, pk):
        evolucion = get_object_or_404(
            EvolucionClinica.objects.select_related(
                "id_cita__id_paciente__id_persona",
                "id_cita__id_odontologo__id_usuario__id_persona",
                "id_cita__id_box",
            ).prefetch_related("adjuntos"),
            pk=pk,
        )
        return render(request, self.template_name, {"evolucion": evolucion})


class EvolucionEditarView(LoginRequeridoMixin, View):
    template_name = "fichas/evolucion_form.html"

    def get(self, request, pk):
        evolucion = get_object_or_404(EvolucionClinica.objects.select_related("id_cita__id_paciente__id_persona"), pk=pk)
        if not puede_atender_cita(request.user, evolucion.id_cita):
            raise PermissionDenied("No tienes permisos para editar esta evolucion.")
        return render(request, self.template_name, {
            "evolucion": evolucion,
            "cita": evolucion.id_cita,
            "editar": True,
        })

    def post(self, request, pk):
        evolucion = get_object_or_404(EvolucionClinica, pk=pk)
        if not puede_atender_cita(request.user, evolucion.id_cita):
            raise PermissionDenied("No tienes permisos para editar esta evolucion.")
        datos = _datos_evolucion_desde_post(request)
        datos_anteriores = {campo: getattr(evolucion, campo, None) for campo in datos}
        for campo, valor in datos.items():
            setattr(evolucion, campo, valor)
        evolucion.save()
        Bitacora.registrar(
            usuario=request.user, modulo="fichas", accion="edicion",
            tabla_afectada="evoluciones_clinicas", id_registro_afectado=evolucion.id_evolucion,
            descripcion=f"Evolución #{evolucion.id_evolucion} editada",
            ip_origen=getattr(request, "ip_origen", None),
        )
        messages.success(request, "Evolución actualizada correctamente.")
        return redirect("fichas:evolucion_detalle", pk=pk)


class AdjuntoSubirView(LoginRequeridoMixin, View):
    def post(self, request, pk):
        evolucion = get_object_or_404(EvolucionClinica, pk=pk)
        if not puede_atender_cita(request.user, evolucion.id_cita):
            raise PermissionDenied("No tienes permisos para adjuntar archivos clinicos.")
        archivo = request.FILES.get("archivo")
        if not archivo:
            messages.error(request, "No se seleccionó ningún archivo.")
            return redirect("fichas:evolucion_detalle", pk=pk)
        adj = AdjuntoClinico(
            id_evolucion=evolucion,
            nombre_archivo=archivo.name,
            tipo_mime=archivo.content_type or "application/octet-stream",
            tamano_kb=round(archivo.size / 1024, 2),
            id_usuario_sube=request.user,
        )
        adj.ruta_archivo.save(archivo.name, archivo, save=True)
        messages.success(request, f"Archivo '{archivo.name}' subido correctamente.")
        return redirect("fichas:evolucion_detalle", pk=pk)
