# user_stories.md — SENTIO: Historias de Usuario

> **Versión:** 1.0.0 · **Fecha:** Mayo 2026
> **Product Owner:** Proyecto de Curso — PTIA Grupo 3
> **Metodología:** Agile / Scrum · Priorización MoSCoW · Criterios en Gherkin

---

## Roles del Sistema

| Rol | Descripción |
|---|---|
| **Estudiante** | Usuario principal. Registra su estado emocional diario y consulta su análisis de bienestar. |
| **Consejero** | Psicólogo o asesor universitario. Consulta reportes agregados y recibe alertas de riesgo alto. |
| **Administrador** | Gestiona usuarios, configuración del sistema y monitorea la salud técnica de la plataforma. |

---

## Leyenda de Priorización MoSCoW

| Etiqueta | Significado |
|---|---|
| 🔴 **Must have** | Crítico para el MVP. Sin esto, el sistema no funciona. |
| 🟡 **Should have** | Importante, pero el MVP puede operar sin ello temporalmente. |
| 🟢 **Could have** | Deseable si el tiempo lo permite. Agrega valor sin ser esencial. |
| ⚪ **Won't have** | Fuera del alcance de esta iteración. Documentado para el backlog futuro. |

---

## Épica 1 — Onboarding y Configuración de Perfil

---

### US-01 · Registro inicial del perfil estudiantil

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **configurar mi perfil académico al ingresar por primera vez** (edad, carrera, semestre y hábitos base), para poder **recibir recomendaciones y análisis personalizados desde el primer día**.

**Criterios de aceptación:**

```gherkin
Feature: Configuración inicial de perfil

  Scenario: Estudiante completa el onboarding con todos los campos
    Given que el estudiante accede a SENTIO por primera vez
    And no existe un perfil asociado a su sesión
    When completa los campos de edad, carrera y semestre
    And ajusta los sliders de horas de sueño habituales, actividad física y estrés académico base
    And presiona "Crear mi perfil"
    Then el sistema persiste el perfil en la base de datos
    And redirige al estudiante a la pantalla de inicio
    And muestra un mensaje de bienvenida personalizado con su nombre de carrera

  Scenario: Estudiante intenta continuar sin completar campos obligatorios
    Given que el estudiante está en la pantalla de onboarding
    When deja el campo "Carrera" vacío
    And presiona "Crear mi perfil"
    Then el sistema muestra un mensaje de validación inline bajo el campo vacío
    And no navega a ninguna otra pantalla
    And no crea ningún registro en la base de datos

  Scenario: Estudiante ya tiene perfil creado e intenta acceder al onboarding
    Given que el estudiante tiene un perfil existente en el sistema
    When intenta navegar manualmente a la URL de onboarding
    Then el sistema lo redirige automáticamente a la pantalla de inicio
    And no sobrescribe su perfil existente
```

---

### US-02 · Inicio de sesión seguro

**Prioridad:** 🔴 Must have
**Rol:** Estudiante / Consejero / Administrador

> Como **usuario del sistema**, quiero **autenticarme con mis credenciales institucionales**, para poder **acceder solo a mis propios datos y proteger mi privacidad**.

**Criterios de aceptación:**

```gherkin
Feature: Autenticación de usuarios

  Scenario: Inicio de sesión exitoso
    Given que el usuario tiene una cuenta registrada en SENTIO
    When ingresa su correo institucional y contraseña correctos
    And presiona "Ingresar"
    Then el sistema genera un token JWT con expiración de 8 horas
    And redirige al usuario a la pantalla correspondiente a su rol
    And no expone el token en la URL ni en logs del sistema

  Scenario: Contraseña incorrecta
    Given que el usuario existe en el sistema
    When ingresa su correo correcto pero una contraseña incorrecta
    And presiona "Ingresar"
    Then el sistema muestra el mensaje "Credenciales incorrectas. Intenta de nuevo."
    And no especifica cuál campo es incorrecto (seguridad anti-enumeración)
    And registra el intento fallido con timestamp e IP en el log de auditoría

  Scenario: Bloqueo por intentos fallidos repetidos
    Given que el usuario ha fallado el inicio de sesión 5 veces consecutivas
    When intenta iniciar sesión una vez más
    Then el sistema bloquea la cuenta por 15 minutos
    And muestra un mensaje indicando el tiempo de bloqueo
    And envía una notificación al correo del usuario sobre el bloqueo
```

---

## Épica 2 — Registro Diario (Core del Sistema)

---

### US-03 · Registro diario de estado emocional en menos de 2 minutos

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **registrar mi estado emocional del día en menos de 2 minutos usando controles visuales intuitivos**, para poder **mantener el hábito diario sin que se convierta en una carga adicional**.

**Criterios de aceptación:**

```gherkin
Feature: Registro diario ágil

  Scenario: Estudiante completa el registro diario completo
    Given que el estudiante está autenticado
    And no ha registrado el día de hoy
    When selecciona su estado de ánimo en la escala visual de emojis (1-5)
    And selecciona su nivel de energía (1-5)
    And ajusta el slider de horas de sueño entre 4h y 12h
    And ajusta el slider de nivel de estrés entre 1 y 10
    And selecciona al menos una actividad del día (estudio, ejercicio, descanso, social)
    And presiona "Guardar mi día"
    Then el sistema persiste el registro con timestamp automático
    And muestra una pantalla de confirmación con resumen de los valores ingresados
    And el flujo completo no toma más de 2 minutos en condiciones normales de uso

  Scenario: Estudiante intenta registrar el mismo día dos veces
    Given que el estudiante ya completó su registro de hoy
    When navega al formulario de registro diario
    Then el sistema muestra su resumen del día actual
    And ofrece la opción "Editar registro de hoy" (disponible solo hasta las 23:59 del mismo día)
    And no crea un registro duplicado

  Scenario: Estudiante edita el registro del día actual
    Given que el estudiante ya registró hoy y está dentro del mismo día calendario
    When modifica el nivel de estrés de 3 a 7
    And presiona "Guardar cambios"
    Then el sistema actualiza el registro existente (no crea uno nuevo)
    And marca el registro con flag "editado: true" y timestamp de edición
    And recalcula el análisis de riesgo con los valores actualizados

  Scenario: Estudiante intenta registrar un día anterior (registro retroactivo)
    Given que el estudiante navega al formulario de registro
    When intenta cambiar manualmente la fecha a un día anterior
    Then el sistema permite el registro retroactivo solo si la fecha es de ayer (máximo 24h de diferencia)
    And marca automáticamente el registro con flag "retroactivo: true"
    And muestra una advertencia: "Los registros retroactivos tienen menor peso en tu análisis"
    And rechaza cualquier fecha anterior a ayer con mensaje de error
```

---

### US-04 · Recordatorio diario no intrusivo

**Prioridad:** 🟡 Should have
**Rol:** Estudiante

> Como **estudiante**, quiero **recibir un recordatorio configurable al final del día**, para poder **mantener la consistencia en mis registros sin necesitar recordarlo yo mismo**.

**Criterios de aceptación:**

```gherkin
Feature: Recordatorios de registro diario

  Scenario: Estudiante configura el horario del recordatorio
    Given que el estudiante está en la sección de configuración
    When selecciona "Recordatorio diario" y elige las 9:30 PM
    And activa el toggle de notificaciones
    Then el sistema guarda la preferencia asociada a su perfil
    And confirma con un mensaje "Recibirás tu recordatorio a las 9:30 PM"

  Scenario: Sistema envía recordatorio cuando el estudiante no ha registrado
    Given que son las 9:30 PM y el estudiante no ha completado su registro de hoy
    When el sistema ejecuta el job de recordatorios programado
    Then envía una notificación push con el mensaje "¿Cómo estuvo tu día? Tómate 2 minutos para registrarlo 🌙"
    And la notificación incluye un enlace directo al formulario de registro
    And no envía el recordatorio si el estudiante ya registró el día

  Scenario: Estudiante con 3 días consecutivos sin registro
    Given que el estudiante lleva 3 días sin registrar
    When el sistema detecta la brecha en el job nocturno
    Then envía una notificación especial: "Te hemos extrañado. Tu bienestar importa — retoma tu racha hoy"
    And no genera una evaluación de riesgo hasta que el estudiante retome el registro
    And muestra en la app el estado "Datos insuficientes para análisis" en lugar de un nivel de riesgo
```

---

### US-05 · Indicador de calidad de datos en tiempo real

**Prioridad:** 🟡 Should have
**Rol:** Estudiante

> Como **estudiante**, quiero **ver un indicador de cuántos días he registrado en la semana actual**, para poder **saber si mi análisis de IA tendrá suficiente información para ser confiable**.

**Criterios de aceptación:**

```gherkin
Feature: Indicador de calidad de datos

  Scenario: Estudiante con registros suficientes
    Given que el estudiante ha registrado 5 o más de los últimos 7 días
    When accede a la pantalla de análisis
    Then el sistema muestra el indicador de confianza en color verde
    And muestra el texto "Análisis de alta confianza · 5/7 días registrados"
    And presenta la clasificación de riesgo normalmente

  Scenario: Estudiante con registros insuficientes
    Given que el estudiante ha registrado menos de 5 de los últimos 7 días
    When accede a la pantalla de análisis
    Then el sistema muestra el indicador de confianza en color amarillo
    And muestra el texto "Análisis preliminar · Registra más días para mayor precisión"
    And presenta una clasificación de riesgo preliminar con advertencia visible

  Scenario: Estudiante nuevo con menos de 3 días de registro
    Given que el estudiante tiene menos de 3 días de registro en total
    When accede a la pantalla de análisis
    Then el sistema no muestra ninguna clasificación de riesgo
    And muestra el mensaje "Necesitamos al menos 3 días de registros para comenzar tu análisis"
    And muestra una barra de progreso visual: "3 de 7 días para tu primer análisis"
```

---

## Épica 3 — Análisis de IA y Evaluación de Riesgo

---

### US-06 · Consultar evaluación de riesgo emocional semanal

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **ver mi nivel de riesgo emocional calculado por la IA al finalizar mi registro**, para poder **entender si mi bienestar está en un estado saludable o si necesito tomar acciones**.

**Criterios de aceptación:**

```gherkin
Feature: Evaluación de riesgo emocional

  Scenario: Clasificación de riesgo bajo
    Given que el estudiante tiene 5+ días registrados en la última semana
    And sus promedios son: ánimo ≥ 3.5, estrés ≤ 5, sueño ≥ 6h, energía ≥ 3
    When solicita ver su evaluación
    Then el sistema muestra el nivel "Riesgo Bajo" con indicador verde
    And muestra el mensaje motivacional "¡Excelente! Tu bienestar muestra indicadores positivos"
    And lista los 3 factores que más influyeron en la evaluación
    And el tiempo de respuesta de la API es menor a 1 segundo

  Scenario: Clasificación de riesgo medio
    Given que el estudiante tiene patrones de deterioro moderado (estrés creciente o sueño disminuyendo)
    When solicita ver su evaluación
    Then el sistema muestra el nivel "Riesgo Medio" con indicador amarillo
    And muestra una explicación en lenguaje no clínico de los factores detectados
    And presenta recomendaciones específicas para el nivel medio
    And incluye el disclaimer ético visible

  Scenario: Clasificación de riesgo alto
    Given que el estudiante tiene indicadores severos (caída abrupta de ánimo ≥ 2 puntos en un día O sueño < 5h por ≥ 3 días consecutivos)
    When el sistema procesa su análisis
    Then muestra el nivel "Riesgo Alto" con indicador rojo
    And muestra recursos de apoyo inmediatos (orientación psicológica universitaria, línea de escucha)
    And genera una alerta interna para el consejero asignado (si existe)
    And registra el evento en la tabla risk_assessments con decision_source apropiado

  Scenario: Regla clínica detecta deterioro súbito (EC-08)
    Given que el ánimo del estudiante cayó ≥ 2 puntos respecto a su promedio previo en el día de hoy
    And su nivel de estrés es ≥ 4/5
    When el sistema ejecuta la capa de reglas clínicas
    Then fuerza la clasificación a "Riesgo Alto" independientemente del resultado del modelo ML
    And registra decision_source = "clinical_rules" y rule_code = "CRITICAL_ACUTE_DROP"
    And presenta los recursos de crisis en la pantalla de resultado
```

---

### US-07 · Visualizar tendencias emocionales de las últimas semanas

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **ver una gráfica de mis tendencias de ánimo, estrés y sueño de los últimos 7 días**, para poder **identificar yo mismo los patrones en mi bienestar antes de que se conviertan en un problema**.

**Criterios de aceptación:**

```gherkin
Feature: Visualización de tendencias

  Scenario: Estudiante consulta gráfica semanal con datos completos
    Given que el estudiante tiene 7 días de registros consecutivos
    When accede a la sección "Mi análisis" → "Ver tendencias"
    Then el sistema muestra una gráfica de líneas con ánimo, estrés, sueño y energía
    And el eje X muestra los días de la semana (Lun a Dom)
    And el eje Y muestra los valores en escala 1-10 (normalizada)
    And cada línea tiene un color y patrón distintos para ser accesible sin depender solo del color
    And la gráfica incluye una leyenda con los valores promedio de la semana

  Scenario: Estudiante consulta gráfica con días faltantes
    Given que el estudiante tiene 5 de 7 días registrados (faltan 2 días)
    When accede a la gráfica semanal
    Then el sistema muestra los días con registro como puntos sólidos en la gráfica
    And los días sin registro aparecen como puntos vacíos con línea discontinua
    And muestra una nota: "Los días sin registro aparecen interpolados y no afectan tu análisis"

  Scenario: Estudiante alterna entre vista semanal y vista mensual
    Given que el estudiante tiene más de 7 días de historial
    When selecciona "Vista mensual" en el selector de período
    Then la gráfica actualiza su escala temporal a los últimos 30 días
    And el tiempo de actualización de la gráfica es menor a 500ms
    And los promedios del resumen se recalculan para el período seleccionado
```

---

### US-08 · Comprender los factores que determinaron mi nivel de riesgo

**Prioridad:** 🟡 Should have
**Rol:** Estudiante

> Como **estudiante**, quiero **ver una explicación en lenguaje simple de por qué el sistema me clasificó en determinado nivel de riesgo**, para poder **confiar en la evaluación y saber en qué aspectos enfocarme**.

**Criterios de aceptación:**

```gherkin
Feature: Explicabilidad del modelo de IA

  Scenario: Estudiante consulta la explicación de su evaluación
    Given que el estudiante acaba de recibir una clasificación de riesgo
    When presiona "¿Por qué este resultado?"
    Then el sistema muestra los 3 factores con mayor peso en la decisión
    And cada factor se presenta en lenguaje no técnico (ej. "Tu nivel de estrés ha estado por encima de 7/10 durante 4 días")
    And muestra el nivel de confianza de la evaluación en porcentaje visible
    And si la decisión fue por reglas clínicas, lo indica con "Alerta detectada automáticamente"

  Scenario: Clasificación con baja confianza del modelo
    Given que el modelo generó una clasificación con confidence_score < 0.60
    When el estudiante ve su evaluación
    Then el sistema muestra un indicador "Confianza: Moderada"
    And agrega la nota "Registra más días para obtener un análisis más preciso"
    And no oculta el resultado, solo lo contextualiza apropiadamente

  Scenario: Decisión tomada por reglas clínicas (no por el modelo ML)
    Given que una regla clínica forzó la clasificación
    When el estudiante consulta la explicación
    Then el sistema muestra "Detectamos un cambio significativo en tu bienestar hoy"
    And no expone términos técnicos como "rule_code" o "clinical_rules"
    And presenta directamente los recursos de apoyo como acción prioritaria
```

---

## Épica 4 — Recomendaciones Personalizadas

---

### US-09 · Recibir recomendaciones adaptadas a mi nivel de riesgo

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **recibir recomendaciones concretas y accionables adaptadas a mi situación específica**, para poder **mejorar mi bienestar con acciones realistas dentro de mi rutina académica**.

**Criterios de aceptación:**

```gherkin
Feature: Recomendaciones personalizadas

  Scenario: Recomendaciones para riesgo bajo
    Given que el estudiante tiene clasificación de riesgo bajo
    When accede a la sección de recomendaciones
    Then el sistema muestra entre 2 y 3 tarjetas de recomendación de mantenimiento
    And las recomendaciones refuerzan los hábitos positivos detectados (ej. si el ejercicio es frecuente, lo destaca)
    And no incluye lenguaje alarmante ni referencias clínicas

  Scenario: Recomendaciones para riesgo medio
    Given que el estudiante tiene clasificación de riesgo medio
    When accede a la sección de recomendaciones
    Then el sistema muestra entre 3 y 5 tarjetas con acciones específicas
    And al menos una recomendación aborda el factor de mayor peso en la clasificación
    And ofrece el enlace a orientación psicológica universitaria como opción (no obligatoria)
    And las recomendaciones incluyen micro-acciones (ej. "20 minutos de caminata hoy")

  Scenario: Recomendaciones para riesgo alto
    Given que el estudiante tiene clasificación de riesgo alto
    When accede a la sección de recomendaciones
    Then el sistema muestra como primera tarjeta los recursos de apoyo inmediato (línea de escucha, bienestar universitario)
    And el botón de acción principal dice "Hablar con alguien ahora"
    And las recomendaciones de autocuidado se presentan como complemento, no como sustituto de apoyo profesional
    And el disclaimer ético es prominente y visible sin necesidad de scroll

  Scenario: Recomendaciones no se repiten exactamente en días consecutivos
    Given que el estudiante consulta sus recomendaciones hoy y mañana con el mismo nivel de riesgo
    When el sistema genera las recomendaciones para cada día
    Then al menos el 50% de las tarjetas son distintas entre ambos días
    And la variación evita la fatiga de contenido repetitivo
```

---

### US-10 · Acceder a recursos de apoyo en cualquier momento

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **poder acceder a los recursos de apoyo psicológico institucional desde cualquier pantalla de la app**, para poder **buscar ayuda rápidamente sin tener que navegar varios menús en un momento de crisis**.

**Criterios de aceptación:**

```gherkin
Feature: Acceso rápido a recursos de apoyo

  Scenario: Estudiante accede a recursos desde el menú principal
    Given que el estudiante está en cualquier pantalla de la aplicación
    When presiona el ícono de corazón/ayuda en la barra de navegación
    Then el sistema muestra una pantalla con recursos de apoyo en menos de 200ms
    And los recursos incluyen: nombre del servicio, teléfono, correo y horario de atención
    And el teléfono es un enlace directo a marcación (tel: protocol)

  Scenario: Recursos disponibles sin conexión a internet
    Given que el estudiante no tiene conexión a internet
    When intenta acceder a la sección de recursos de apoyo
    Then el sistema muestra los recursos desde caché local (guardados al último inicio de sesión)
    And muestra una nota discreta "Información guardada localmente — verifica disponibilidad"

  Scenario: Disclaimer ético siempre visible en evaluaciones de riesgo
    Given que el estudiante está viendo cualquier evaluación de riesgo
    When observa la pantalla de resultado
    Then el texto "Esta evaluación es orientativa y no constituye un diagnóstico clínico" es visible sin necesidad de scroll
    And el texto tiene un contraste de color mínimo de 4.5:1 (WCAG AA)
```

---

## Épica 5 — Panel del Consejero

---

### US-11 · Recibir alertas de estudiantes con riesgo alto

**Prioridad:** 🔴 Must have
**Rol:** Consejero

> Como **consejero universitario**, quiero **recibir una notificación cuando un estudiante asignado alcance el nivel de riesgo alto**, para poder **priorizar mi atención hacia los casos más urgentes de manera oportuna**.

**Criterios de aceptación:**

```gherkin
Feature: Alertas de riesgo alto para consejeros

  Scenario: Sistema genera alerta automática por riesgo alto
    Given que un estudiante asignado al consejero recibe clasificación de riesgo alto
    When el sistema procesa la evaluación
    Then genera una notificación interna para el consejero en menos de 30 segundos
    And la notificación incluye: identificador anónimo del estudiante, fecha, nivel de riesgo y factor principal
    And NO incluye el contenido literal de los registros del estudiante (privacidad)
    And registra la alerta en el log de auditoría con timestamp

  Scenario: Consejero consulta la lista de alertas activas
    Given que el consejero está autenticado en su panel
    When accede a la sección "Alertas activas"
    Then ve la lista de estudiantes con riesgo alto o medio persistente (≥3 días)
    And la lista está ordenada por severidad y fecha (más urgentes primero)
    And puede marcar una alerta como "Atendida" con una nota de seguimiento

  Scenario: Estudiante no ha dado consentimiento para compartir datos con consejero
    Given que un estudiante no ha aceptado explícitamente compartir sus datos con el servicio de bienestar
    When su evaluación alcanza riesgo alto
    Then el sistema NO genera alerta para el consejero
    And registra internamente el evento para métricas agregadas anonimizadas
    And muestra al estudiante los recursos de apoyo de forma autónoma
```

---

### US-12 · Ver reporte agregado de bienestar del grupo estudiantil

**Prioridad:** 🟡 Should have
**Rol:** Consejero

> Como **consejero universitario**, quiero **ver estadísticas agregadas y anonimizadas del bienestar del grupo**, para poder **identificar tendencias poblacionales y planificar intervenciones preventivas grupales**.

**Criterios de aceptación:**

```gherkin
Feature: Reporte agregado de bienestar grupal

  Scenario: Consejero consulta el dashboard grupal
    Given que el consejero está autenticado
    When accede a "Reporte grupal"
    Then ve el porcentaje de estudiantes por nivel de riesgo (Bajo/Medio/Alto) para la semana actual
    And ve la tendencia comparada con la semana anterior (mejora/deterioro del grupo)
    And todos los datos son completamente anonimizados (sin identificadores individuales)
    And el reporte incluye la nota "Basado en N estudiantes con consentimiento activo"

  Scenario: Grupo con menos de 5 estudiantes activos
    Given que menos de 5 estudiantes del grupo tienen registros activos esta semana
    When el consejero intenta ver el reporte grupal
    Then el sistema no muestra estadísticas para proteger la privacidad individual
    And muestra el mensaje "Datos insuficientes para el reporte grupal esta semana (mínimo 5 estudiantes activos)"

  Scenario: Exportación del reporte para informes institucionales
    Given que el consejero necesita incluir datos en un informe institucional
    When selecciona "Exportar reporte" y elige el rango de fechas
    Then el sistema genera un PDF con estadísticas agregadas anonimizadas
    And el PDF incluye en el encabezado: fecha de generación, período analizado y número de participantes
    And el PDF incluye el disclaimer de limitaciones del sistema
```

---

## Épica 6 — Administración del Sistema

---

### US-13 · Gestionar usuarios y asignaciones de consejería

**Prioridad:** 🟡 Should have
**Rol:** Administrador

> Como **administrador**, quiero **crear cuentas de usuario, asignar estudiantes a consejeros y desactivar cuentas inactivas**, para poder **mantener el sistema organizado y garantizar que las alertas lleguen a la persona correcta**.

**Criterios de aceptación:**

```gherkin
Feature: Gestión de usuarios por el administrador

  Scenario: Administrador crea un nuevo consejero
    Given que el administrador está en el panel de administración
    When ingresa el correo institucional, nombre y rol "Consejero"
    And presiona "Crear usuario"
    Then el sistema crea la cuenta con contraseña temporal
    And envía un correo al nuevo consejero con instrucciones de primer acceso
    And el nuevo consejero aparece en la lista con estado "Pendiente de activación"

  Scenario: Administrador asigna estudiantes a un consejero
    Given que existen estudiantes sin consejero asignado
    When el administrador selecciona un grupo de estudiantes y elige un consejero del dropdown
    And confirma la asignación
    Then el sistema actualiza la relación estudiante-consejero en la base de datos
    And el consejero comienza a recibir alertas de los estudiantes asignados
    And los estudiantes afectados reciben notificación informando que tienen un consejero asignado

  Scenario: Desactivar cuenta de estudiante que se graduó o se retiró
    Given que un estudiante ya no pertenece a la institución
    When el administrador desactiva su cuenta
    Then el estudiante pierde acceso inmediato al sistema
    And sus datos históricos se conservan durante 1 año por política de retención
    And el consejero asignado recibe notificación de que el estudiante fue desactivado
```

---

### US-14 · Monitorear la salud técnica del sistema

**Prioridad:** 🟡 Should have
**Rol:** Administrador

> Como **administrador**, quiero **ver métricas de uso y estado del sistema en tiempo real**, para poder **detectar problemas técnicos antes de que afecten a los usuarios**.

**Criterios de aceptación:**

```gherkin
Feature: Monitoreo técnico del sistema

  Scenario: Administrador consulta el estado del sistema
    Given que el administrador accede al panel de administración
    When navega a "Salud del sistema"
    Then ve el estado del endpoint GET /health (operativo / degradado / caído)
    And ve el tiempo de respuesta promedio de la API en los últimos 60 minutos
    And ve el porcentaje de predicciones completadas exitosamente vs fallidas
    And los datos se actualizan cada 60 segundos automáticamente

  Scenario: El tiempo de inferencia del modelo supera el umbral aceptable
    Given que el tiempo promedio de respuesta del endpoint /analysis supera 1000ms
    When el sistema detecta la anomalía en el monitoreo
    Then genera una alerta interna para el administrador
    And registra el evento en el log con timestamp, endpoint afectado y tiempo de respuesta
    And el usuario final recibe el resultado igual (sin degradación visible), con procesamiento en background si es necesario
```

---

## Épica 7 — Privacidad, Consentimiento y Ética

---

### US-15 · Gestionar mis preferencias de privacidad y consentimiento

**Prioridad:** 🔴 Must have
**Rol:** Estudiante

> Como **estudiante**, quiero **controlar qué datos se comparten con el servicio de bienestar universitario y poder revocar ese consentimiento en cualquier momento**, para poder **usar la aplicación con confianza de que mis datos de salud mental son míos**.

**Criterios de aceptación:**

```gherkin
Feature: Control de privacidad y consentimiento

  Scenario: Estudiante otorga consentimiento para compartir datos con consejería
    Given que el estudiante está en la configuración de privacidad
    When activa el toggle "Compartir alertas con mi consejero de bienestar"
    And acepta la explicación de qué datos se compartirán (solo nivel de riesgo y factores generales, no registros literales)
    Then el sistema registra el consentimiento con timestamp y versión del documento aceptado
    And el consejero asignado comienza a recibir alertas si el riesgo es alto

  Scenario: Estudiante revoca el consentimiento de compartir datos
    Given que el estudiante había dado consentimiento previamente
    When desactiva el toggle de consentimiento y confirma la revocación
    Then el sistema marca el consentimiento como revocado con timestamp
    And el consejero deja de recibir alertas de ese estudiante de manera inmediata
    And el sistema muestra la confirmación: "Tus datos ya no se comparten con el servicio de consejería"

  Scenario: Estudiante solicita eliminar todos sus datos
    Given que el estudiante quiere ejercer su derecho de supresión (Ley 1581)
    When navega a "Mi cuenta" → "Eliminar mis datos" y confirma con su contraseña
    Then el sistema elimina todos sus registros diarios, evaluaciones y perfil
    And envía confirmación de eliminación al correo del estudiante
    And el proceso de eliminación completa en menos de 48 horas
    And se conserva únicamente un registro anonimizado de la solicitud de eliminación (cumplimiento legal)
```

---

### US-16 · Ver el historial de mis evaluaciones anteriores

**Prioridad:** 🟢 Could have
**Rol:** Estudiante

> Como **estudiante**, quiero **revisar mis evaluaciones de riesgo de semanas anteriores**, para poder **ver mi progreso en el tiempo y reconocer períodos difíciles que ya superé**.

**Criterios de aceptación:**

```gherkin
Feature: Historial de evaluaciones

  Scenario: Estudiante consulta el historial de evaluaciones
    Given que el estudiante tiene más de 2 semanas de uso de la aplicación
    When accede a "Mi historial"
    Then ve una línea de tiempo con sus evaluaciones semanales anteriores
    And cada evaluación muestra: fecha, nivel de riesgo y emoji representativo
    And puede seleccionar cualquier semana pasada para ver el desglose de factores

  Scenario: Historial muestra períodos de mejora significativa
    Given que el estudiante pasó de riesgo alto a riesgo bajo en un período de 2 semanas
    When consulta esa transición en el historial
    Then el sistema resalta visualmente la mejora con un ícono de progreso positivo
    And muestra el mensaje "¡Superaste un período difícil! Tu resiliencia es notable"
```

---

## Épica 8 — Experiencia de Usuario y Accesibilidad

---

### US-17 · Usar la aplicación en modo oscuro

**Prioridad:** 🟢 Could have
**Rol:** Estudiante

> Como **estudiante**, quiero **que la aplicación respete la preferencia de modo oscuro de mi dispositivo**, para poder **usarla cómodamente por la noche sin lastimar mi vista al registrar antes de dormir**.

**Criterios de aceptación:**

```gherkin
Feature: Soporte de modo oscuro

  Scenario: Sistema detecta preferencia de modo oscuro del dispositivo
    Given que el dispositivo del estudiante tiene el modo oscuro activado en el sistema operativo
    When el estudiante abre SENTIO
    Then la interfaz aplica el tema oscuro automáticamente
    And todos los textos mantienen un contraste mínimo de 4.5:1 en modo oscuro (WCAG AA)
    And los colores de semáforo de riesgo (verde/amarillo/rojo) son distinguibles en ambos modos

  Scenario: Estudiante cambia el tema manualmente desde la app
    Given que el estudiante está en configuración
    When selecciona "Tema claro" aunque su sistema esté en modo oscuro
    Then la app aplica el tema claro y lo persiste en sus preferencias
    And la preferencia de la app tiene prioridad sobre la preferencia del sistema operativo
```

---

### US-18 · Aplicación funciona con conexión intermitente

**Prioridad:** 🟢 Could have
**Rol:** Estudiante

> Como **estudiante universitario**, quiero **poder completar mi registro diario aunque tenga conexión lenta o intermitente**, para poder **mantener mi hábito de registro en zonas con mala señal dentro del campus**.

**Criterios de aceptación:**

```gherkin
Feature: Funcionamiento offline / baja conectividad

  Scenario: Estudiante completa registro sin conexión
    Given que el estudiante no tiene conexión a internet
    When completa el formulario de registro diario y presiona "Guardar mi día"
    Then el sistema guarda el registro localmente en el dispositivo
    And muestra el mensaje "Registro guardado localmente — se sincronizará cuando haya conexión"
    And el ícono de estado muestra el modo offline claramente

  Scenario: Sincronización automática al recuperar conexión
    Given que el estudiante tiene uno o más registros guardados offline
    When el dispositivo recupera conexión a internet
    Then el sistema sincroniza automáticamente los registros pendientes con el servidor
    And muestra una notificación breve "Tus registros han sido sincronizados"
    And los registros sincronizados mantienen la fecha y hora original del registro offline
```

---

## Backlog — Won't Have (Esta Iteración)

Las siguientes historias están documentadas para el backlog futuro pero quedan **fuera del alcance del MVP actual**:

| ID | Historia | Razón de exclusión |
|---|---|---|
| WH-01 | Integración con calendario académico universitario para contextualizar períodos de exámenes | Requiere integración con sistemas institucionales externos — fuera del alcance académico |
| WH-02 | Análisis de texto libre en entradas de diario personal usando NLP | Requiere modelo de lenguaje adicional (BERT/embeddings) — complejidad fuera del alcance del curso |
| WH-03 | Notificaciones push nativas en dispositivos iOS/Android | Requiere app móvil nativa o PWA — el MVP usa Streamlit web |
| WH-04 | Comparación anónima del bienestar propio vs. promedios de la carrera | Requiere masa crítica de usuarios y análisis de privacidad diferencial más profundo |
| WH-05 | Módulo de meditación guiada y ejercicios de respiración integrados | Fuera del alcance de ingeniería de IA — corresponde a una capa de contenido especializado |

---

## Resumen de Priorización

| Prioridad | Cantidad | IDs |
|---|---|---|
| 🔴 Must have | 8 | US-01, US-02, US-03, US-06, US-07, US-09, US-10, US-11, US-15 |
| 🟡 Should have | 5 | US-04, US-05, US-08, US-12, US-13, US-14 |
| 🟢 Could have | 3 | US-16, US-17, US-18 |
| ⚪ Won't have | 5 | WH-01 a WH-05 |

---

## Notas de UX para el Equipo de Desarrollo

1. **La fricción del registro es el riesgo principal.** Si el formulario diario toma más de 2 minutos, el abandono aumentará exponencialmente. Toda decisión de diseño del formulario debe medirse contra este umbral.
2. **El lenguaje nunca es clínico.** Ningún término técnico (features, inference, classification) debe aparecer en la UI. Toda comunicación es en lenguaje cotidiano, cálido y no alarmante.
3. **El riesgo alto no es un castigo.** El diseño visual del nivel alto debe comunicar urgencia sin generar pánico. Priorizar recursos de ayuda sobre la clasificación misma.
4. **El consentimiento es activo, no pasivo.** Nunca pre-marcar casillas de consentimiento de datos. El estudiante debe elegir explícitamente compartir información con consejería.
5. **Los estados vacíos son oportunidades.** Cuando no hay datos suficientes, la UI debe motivar al registro — no mostrar errores vacíos.

---

*Este documento es la fuente de verdad de los requerimientos funcionales de SENTIO. Debe actualizarse al inicio de cada sprint con los cambios acordados en la reunión de refinamiento del backlog.*
