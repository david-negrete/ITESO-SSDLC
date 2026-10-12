# Profile Lab

Aplicación para demostrar cómo integrar casos de prueba de seguridad y escaneos en un pipeline. UI en inglés; guía de clase en español. Solo contiene perfiles sintéticos.

- App: https://profile-security-classroom.onrender.com
- Repositorio: https://github.com/david-negrete/ITESO-SSDLC
- Pipeline: https://github.com/david-negrete/ITESO-SSDLC/actions/workflows/security.yml

## Ejecutar localmente

Requiere Python 3.12 y acceso a PyPI para instalar dependencias.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_local.py
```

Abre http://127.0.0.1:5000. La consola muestra contraseñas temporales para `alice`, `bob` y `admin`. Cada reinicio genera otras. El servidor local escucha únicamente en loopback.

Un usuario puede leer y modificar su propio perfil. Un administrador puede acceder a todos los perfiles. Solo se puede editar `bio`; el cliente no puede cambiar roles ni IDs. Los datos, sesiones y límites de intentos se guardan en memoria y se reinician con el servicio. Por eso el despliegue usa un solo worker. Esta app está diseñada para una demostración pequeña, sin datos reales.

## Ejecutar pruebas y escaneos

```powershell
python scripts/run_tests.py
python -m pip install -r requirements-ci.txt
python -m bandit app.py wsgi.py -f json -o reports/bandit.json
python -m pip_audit -r requirements.txt -f json -o reports/sca.json
```

Los casos tienen IDs visibles, como `TC_AUTHZ_02_other_profile_is_denied`. La matriz en `docs/test-cases.csv` explica precondiciones, acciones, resultados esperados y referencias. El resultado resumido está en `reports/tests.json`.

## Pipeline en GitHub Actions

El repositorio de destino es `david-negrete/ITESO-SSDLC`, con rama principal `main`. Conserva la estructura de carpetas, incluida `.github/`. Se requieren permisos de escritura y GitHub Actions habilitado.

El workflow `Classroom security pipeline` corre en pushes a `main`, pull requests y ejecuciones manuales:

1. **Functional and security test cases:** ejecuta los casos automatizados.
2. **SAST - Bandit:** analiza `app.py` y `wsgi.py`; cualquier hallazgo hace fallar el job.
3. **SCA - pip-audit:** consulta vulnerabilidades conocidas de las dependencias runtime, incluidas las transitivas resueltas. Cualquier vulnerabilidad reportada hace fallar el job.
4. **Secret scanning - Gitleaks:** escanea el historial Git. Los reportes se redactan para no mostrar secretos detectados.
5. **DAST - ZAP:** inicia una app temporal y hace un baseline pasivo de las rutas públicas. Falta de CSP o de X-Content-Type-Options se configura como FAIL; otros avisos quedan en el reporte. Un error del escáner también hace fallar el job.
6. **Deploy:** solo puede correr en `main`, cuando pasan los jobs anteriores y se configura `DEPLOY_ENABLED=true`.

Los jobs de escaneo guardan evidencia descargable como artifacts. SAST, SCA y secretos corren en paralelo con las pruebas. DAST espera a que las pruebas pasen. ZAP no inicia sesión y no verifica los perfiles privados: los casos de autorización cubren ese comportamiento. Un escaneo exitoso no implica cumplimiento completo de ASVS.

Las herramientas de CI se instalan en los runners. No son dependencias de la app. Las versiones de dependencias runtime están fijadas; el contenedor ZAP usa su canal `stable` y las acciones usan tags de versión mayor. Para congelar una clase reproducible a largo plazo, registra/pina los SHA/digests después del primer run exitoso.

## Demostrar la regresión de autorización

En **Actions → Classroom security pipeline → Run workflow**, selecciona `authorization-regression`.

El workflow modifica la condición de autorización únicamente en su checkout temporal. Muestra el diff y ejecuta la misma suite. Deben fallar los casos que impiden leer o editar otro perfil. No cambia el repositorio ni la aplicación pública. DAST y despliegue quedan bloqueados. Después ejecuta `baseline` para mostrar los mismos casos pasando.

Esta comparación representa dos estados de código en runners aislados. No simula una publicación ni inventa resultados de los escáneres.

## Publicar en Render

1. Conecta tu repositorio a Render e importa `render.yaml` como Blueprint. Revisa el plan antes de crear el servicio. El archivo solicita `free`, sujeto a disponibilidad de tu cuenta.
2. Render genera las contraseñas de los tres usuarios y la clave de sesión. Consulta las contraseñas en la configuración del servicio y comparte solo las de las cuentas sintéticas necesarias para la clase.
3. El primer despliegue al crear el servicio se hace desde Render. Los siguientes quedan con auto-deploy apagado, para que los controle GitHub Actions.
4. En GitHub, crea el environment `classroom`. Dentro de él, agrega el secret `RENDER_DEPLOY_HOOK` con el deploy hook de Render, y la variable `APP_URL` con la URL HTTPS del servicio. El hook es un secreto: no lo pegues en archivos, tickets ni chat.
5. En las variables del repositorio, agrega `DEPLOY_ENABLED=true` cuando quieras habilitar los despliegues del pipeline.
6. Ejecuta `baseline` desde `main`. El job solicita a Render desplegar exactamente el commit verificado y consulta `/health` hasta que la revisión coincide y cambia la instancia en ejecución. Esto también comprueba un reinicio cuando se vuelve a desplegar el mismo commit.

No actives `APP_LOCAL_HTTP` en Render. El servicio público exige cookies Secure y HSTS. Sesiones anteriores se invalidan después de un reinicio. Si el primer arranque tarda, abre la app antes de la clase.

## Fuentes

- [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en)
- [WSTG 4.2](https://wstg.owasp.org/v4.2/)
- [GitHub: Python workflows](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [Bandit](https://bandit.readthedocs.io/en/latest/)
- [pip-audit](https://github.com/pypa/pip-audit)
- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [ZAP baseline](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [Render Blueprints](https://render.com/docs/blueprint-spec)
- [Render deploy hooks](https://render.com/docs/deploy-hooks)
