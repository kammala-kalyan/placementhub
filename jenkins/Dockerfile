# Jenkins controller image for the PlacementHub nightly pipeline.
# Python is installed here so pipeline steps run directly, with no Docker
# socket mounted into Jenkins (mounting it would give Jenkins root on the host).
#
# The floating "lts" tag keeps the core new enough for the latest plugins that
# plugins.txt installs. For strict reproducibility you would pin both the
# core version and every plugin version.
FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip git curl \
 && rm -rf /var/lib/apt/lists/* \
 # The repo is mounted read-only and owned by another user; tell git it is safe.
 && git config --system --add safe.directory '*'

USER jenkins

# Plugins and configuration as code: no clicking through the setup wizard.
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true" \
    CASC_JENKINS_CONFIG=/casc/casc.yaml

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD curl -fsS http://localhost:8080/login >/dev/null || exit 1
