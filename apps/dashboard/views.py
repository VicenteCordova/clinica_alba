"""
apps/dashboard/views.py
"""
import json
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q

from apps.core.mixins import LoginRequeridoMixin
from django.views import View


class DashboardView(LoginRequeridoMixin, View):
    """Enruta al dashboard correcto segun el rol."""
    def get(self, request):
        if request.user.is_superuser or request.user.tiene_rol("administrador"):
            return self.dashboard_admin(request)
        elif request.user.tiene_rol("director", "director_clinico"):
            return self.dashboard_admin(request)
        elif request.user.tiene_rol("odontologo"):
            return self.dashboard_odontologo(request)
        elif request.user.tiene_rol("recepcionista", "administrativo", "recepcion"):
            return self.dashboard_recepcion(request)
        elif request.user.tiene_rol("cajero"):
            return self.dashboard_recepcion(request)
        return self.dashboard_admin(request)

    def dashboard_recepcion(self, request):
        hoy = timezone.localdate()
        from apps.agenda.models import Cita
        from apps.caja.models import Caja
        from apps.presupuestos.models import Presupuesto
        from datetime import timedelta

        citas_hoy = Cita.objects.filter(
            fecha_hora_inicio__date=hoy
        ).select_related(
            "id_paciente__id_persona",
            "id_odontologo__id_usuario__id_persona",
            "id_estado_cita", "id_box",
        ).order_by("fecha_hora_inicio")

        # Preview citas mañana
        manana = hoy + timedelta(days=1)
        citas_manana = Cita.objects.filter(
            fecha_hora_inicio__date=manana
        ).select_related(
            "id_paciente__id_persona",
            "id_odontologo__id_usuario__id_persona",
            "id_estado_cita",
        ).order_by("fecha_hora_inicio")[:5]

        # Caja activa del usuario
        caja_activa = Caja.objects.filter(
            id_usuario_apertura=request.user,
            estado_caja="abierta",
        ).first()

        # Presupuestos pendientes de cobro
        presupuestos_pendientes = Presupuesto.objects.filter(
            estado_presupuesto__in=["aceptado", "pagado_parcial"]
        ).count()

        ctx = {
            "citas": citas_hoy,
            "citas_manana": citas_manana,
            "caja_activa": caja_activa,
            "presupuestos_pendientes": presupuestos_pendientes,
            "rol_activo": "recepcionista",
        }
        return render(request, "dashboard/recepcion.html", ctx)

    def dashboard_odontologo(self, request):
        hoy = timezone.localdate()
        from apps.agenda.models import Cita
        citas_hoy = Cita.objects.filter(
            fecha_hora_inicio__date=hoy,
            id_odontologo__id_usuario=request.user,
        ).select_related(
            "id_paciente__id_persona",
            "id_odontologo__id_usuario__id_persona",
            "id_estado_cita", "id_box", "id_tipo_atencion",
        ).order_by("fecha_hora_inicio")

        # Proxima cita pendiente o en espera
        proxima_cita = citas_hoy.filter(
            id_estado_cita__nombre__in=["en_espera", "confirmada", "pendiente"]
        ).first()

        # Ultimas evoluciones del odontologo
        from apps.fichas.models import EvolucionClinica
        ultimas_evoluciones = EvolucionClinica.objects.filter(
            id_cita__id_odontologo__id_usuario=request.user,
        ).select_related(
            "id_cita__id_paciente__id_persona",
            "id_cita__id_odontologo__id_usuario__id_persona",
        ).order_by("-fecha_evolucion")[:5]

        citas_en_espera = citas_hoy.filter(id_estado_cita__nombre="en_espera").count()
        citas_atendidas = citas_hoy.filter(id_estado_cita__nombre="atendida").count()

        # Atenciones sin cerrar (evoluciones sin diagnostico)
        atenciones_pendientes = EvolucionClinica.objects.filter(
            id_cita__id_odontologo__id_usuario=request.user,
            id_cita__id_estado_cita__nombre__in=["en_atencion"],
            diagnostico="",
        ).count()

        # Pacientes activos con plan de tratamiento en curso
        from apps.tratamientos.models import PlanTratamiento
        pacientes_activos = (
            PlanTratamiento.objects.filter(
                id_odontologo__id_usuario=request.user,
                estado_plan="en_curso",
            )
            .select_related("id_ficha_clinica__id_paciente__id_persona")
            .order_by("-fecha_creacion")[:5]
        )

        # Fichas clínicas más recientes del odontólogo
        fichas_recientes = (
            EvolucionClinica.objects.filter(
                id_cita__id_odontologo__id_usuario=request.user,
            )
            .select_related("id_cita__id_paciente__id_persona", "id_cita__id_ficha_clinica")
            .order_by("-fecha_evolucion")
            .values(
                "id_cita__id_ficha_clinica",
                "id_cita__id_paciente__id_persona__nombres",
                "id_cita__id_paciente__id_persona__apellido_paterno",
                "id_cita__id_paciente_id",
            )
            .distinct()[:5]
        )

        ctx = {
            "citas_hoy": citas_hoy,
            "proxima_cita": proxima_cita,
            "citas_en_espera": citas_en_espera,
            "citas_atendidas": citas_atendidas,
            "atenciones_pendientes": atenciones_pendientes,
            "ultimas_evoluciones": ultimas_evoluciones,
            "evoluciones_pendientes": atenciones_pendientes,
            "pacientes_activos": pacientes_activos,
            "fichas_recientes": fichas_recientes,
            "rol_activo": "odontologo",
        }
        return render(request, "dashboard/odontologo.html", ctx)

    def dashboard_admin(self, request):
        hoy = timezone.localdate()
        from apps.agenda.models import Cita
        from apps.caja.models import Caja
        from apps.pagos.models import Pago
        from apps.presupuestos.models import Presupuesto
        from apps.odontologos.models import Odontologo
        from apps.auditoria.models import Bitacora
        from datetime import timedelta
        from django.db.models import Count

        # KPIs básicos
        citas_hoy = Cita.objects.filter(fecha_hora_inicio__date=hoy).count()
        atendidos_hoy = Cita.objects.filter(
            fecha_hora_inicio__date=hoy,
            id_estado_cita__nombre="atendida"
        ).count()
        odontologos_activos = Odontologo.objects.filter(estado_profesional="activo").count()
        presupuestos_vigentes = Presupuesto.objects.filter(
            estado_presupuesto__in=["aceptado", "propuesto"]
        ).count()
        pagos_hoy = Pago.objects.filter(
            fecha_pago__date=hoy,
            estado_pago="vigente",
        ).aggregate(total=Sum("monto"))["total"] or 0

        # Caja del usuario
        caja_usuario = Caja.objects.filter(
            id_usuario_apertura=request.user,
            estado_caja="abierta",
        ).first()

        # ── ANALÍTICA ────────────────────────────────────
        # Ingresos del mes actual
        primer_dia_mes = hoy.replace(day=1)
        ingresos_mes = Pago.objects.filter(
            fecha_pago__date__gte=primer_dia_mes,
            fecha_pago__date__lte=hoy,
            estado_pago="vigente",
        ).aggregate(total=Sum("monto"))["total"] or 0

        # Tasa de no-show (canceladas / total últimos 30 días)
        hace_30 = hoy - timedelta(days=30)
        total_citas_mes = Cita.objects.filter(fecha_hora_inicio__date__gte=hace_30).count()
        citas_canceladas_mes = Cita.objects.filter(
            fecha_hora_inicio__date__gte=hace_30,
            id_estado_cita__nombre="cancelada",
        ).count()
        tasa_no_show = (
            round((citas_canceladas_mes / total_citas_mes) * 100, 1)
            if total_citas_mes > 0 else 0
        )

        # Top 3 odontólogos por citas esta semana
        hace_7 = hoy - timedelta(days=7)
        top_odontologos = (
            Cita.objects.filter(fecha_hora_inicio__date__gte=hace_7)
            .values("id_odontologo__id_usuario__id_persona__nombres",
                    "id_odontologo__id_usuario__id_persona__apellido_paterno")
            .annotate(total=Count("id_cita"))
            .order_by("-total")[:3]
        )

        # Presupuestos aceptados pendientes de pago total
        presupuestos_pendientes_cobro = Presupuesto.objects.filter(
            estado_presupuesto__in=["aceptado", "pagado_parcial"]
        ).count()

        # Ingresos por día últimos 7 días para gráfico de barras
        ingresos_diarios = []
        for i in range(6, -1, -1):
            dia = hoy - timedelta(days=i)
            total_dia = Pago.objects.filter(
                fecha_pago__date=dia,
                estado_pago="vigente",
            ).aggregate(t=Sum("monto"))["t"] or 0
            ingresos_diarios.append({"fecha": str(dia), "label": dia.strftime("%d/%m"), "total": float(total_dia)})

        # Próximas citas
        proximas_citas = Cita.objects.filter(
            fecha_hora_inicio__date__gte=hoy,
        ).select_related(
            "id_paciente__id_persona",
            "id_odontologo__id_usuario__id_persona",
            "id_estado_cita", "id_box",
        ).order_by("fecha_hora_inicio")[:10]

        # Citas semana para gráfico doughnut
        citas_semana = Cita.objects.filter(
            fecha_hora_inicio__date__gte=hace_7,
        ).values("id_estado_cita__nombre").annotate(total=Count("id_cita"))
        citas_semana_json = json.dumps(list(citas_semana))
        ingresos_diarios_json = json.dumps(ingresos_diarios)

        ctx = {
            "citas_hoy": citas_hoy,
            "atendidos_hoy": atendidos_hoy,
            "odontologos_activos": odontologos_activos,
            "presupuestos_vigentes": presupuestos_vigentes,
            "pagos_hoy": pagos_hoy,
            "caja_usuario": caja_usuario,
            "proximas_citas": proximas_citas,
            "citas_semana_json": citas_semana_json,
            # Analítica
            "ingresos_mes": ingresos_mes,
            "tasa_no_show": tasa_no_show,
            "top_odontologos": top_odontologos,
            "presupuestos_pendientes_cobro": presupuestos_pendientes_cobro,
            "ingresos_diarios_json": ingresos_diarios_json,
            "rol_activo": "administrador",
        }
        return render(request, "dashboard/index.html", ctx)

