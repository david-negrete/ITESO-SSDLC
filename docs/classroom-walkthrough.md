# Demo de clase, 15 minutos

## 0–3 min: política y comportamiento

Entra como Alice. Abre Profile 1: respuesta 200. Intenta abrir Profile 2: respuesta 403. Pregunta qué debe pasar antes de ejecutar el segundo caso. La política es explícita: un usuario solo puede acceder a su propio perfil; el instructor tiene rol administrador.

## 3–6 min: de ASVS al caso

Abre `docs/test-cases.csv`. Usa TC-AUTHZ-02. Muestra la relación con ASVS v5.0.0-8.2.2 y WSTG-v42-ATHZ-04. Explica que el requisito establece la expectativa de autorización y WSTG aporta técnicas para investigar referencias a objetos. El caso concreta usuario, recurso, acción y resultado esperado.

Abre el test correspondiente en `tests/test_security.py`: hay una aserción para 403 y otras para verificar que no se devuelve el contenido protegido. No basta con comprobar que la pantalla muestra un mensaje de error.

## 6–10 min: un cambio falla

En Actions ejecuta `authorization-regression`. Abre el diff de la condición de autorización y el job de pruebas. Muestra TC_AUTHZ_02 y TC_AUTHZ_03 fallando. Descarga `test-case-results` si quieres revisar la evidencia fuera del log. El código vulnerable solo existe en el runner de esa ejecución.

Puedes preparar este run antes de clase y abrirlo mientras termina una ejecución en vivo. Usa únicamente evidencia de runs reales; no sustituyas resultados por capturas inventadas.

## 10–13 min: escaneos

Abre un run `baseline` exitoso. Compara Bandit, pip-audit, Gitleaks y ZAP. Explica qué entrada recibe cada herramienta y muestra un artifact real. Bandit no conoce la política de quién puede leer cada perfil. Una prueba de autorización que falla puede aportar evidencia que un escáner genérico no encuentra.

El baseline de ZAP es pasivo y sin autenticación. Revisa las advertencias, aunque no todas bloqueen el job. Distingue una vulnerabilidad, una advertencia y un error del escáner.

## 13–15 min: despliegue

Si Render ya está conectado, abre el job Deploy. Muestra que necesita los jobs previos y que compara la revisión de `/health` con el commit probado. Abre la app y repite acceso permitido/denegado.

Si Render todavía no está conectado, el job aparece omitido. Explícalo tal cual; no presentes ese estado como un despliegue exitoso.

## Preparación

- Verifica credenciales y abre la app antes de iniciar la clase.
- Ten un baseline y una regresión de autorización ejecutados y disponibles.
- Revisa que no se haya agregado un advisory nuevo que haga fallar SCA; actualiza la dependencia y repite el pipeline si ocurre.
- No muestres el deploy hook, la clave de sesión ni la contraseña de administrador en pantalla.
- Reserva SecureEnough para la actividad evaluada. Esta demo usa Profile Lab.
