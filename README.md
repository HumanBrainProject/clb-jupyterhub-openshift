# The Collaboratory's Jupyterhub on Openshift Templates

The Collaboratory is part of the Human Brain Project's infrastructure. This is the template used to deploy Jupyterhub on Openshift within the Collaboratory. It provides integration with the Collaboratory's drive (Seafile based shared storage).

This template is based on the [juptyerhub-on-openshift](https://github.com/jupyter-on-openshift/jupyter-quickstart) templates by Graham Dumpleton.

The notebook deployment adds a sidecar container to users' notebook pods which runs the Seadrive daemon to do a fuse mount on the user's drive. This mount is shared with the notebook container.

## Deployment

### Prerequisits

- An Openshift instance where you have an admin account.
- A (Seafile)[https://www.seafile.com/en/home/) installation with a patched version of Seahub to enable token retrieval from OAuth
- Keycloak or another IdP with claims identifying the user.

### Deployment

Setup the OIDC client info:
```
cp config/oauth.env.sample config/oauth.env
$EDITOR  config/oauth.env
```

Login to openshift and create a project:
```
oc login <key> # You can obtain this from the web app.
oc new project jupyterhub-env
```

Setup the templates for Jupyterhub from Jupyterhub on Openshift. These provide the templates

PROD
```
export CLB_ENV='prod'
export CLB_ENV_POSTFIX=''
```

DEV
```
export CLB_ENV='dev'
export CLB_ENV_POSTFIX='-dev'
```

```
export JOO_VERSION="3.4.0"
export CLB_HUB_VERSION=v0.2.1-openshift
export CLB_NB_VERSION=v0.3.5-openshift

oc apply -f image-streams/jupyterhub.json

oc apply -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/$JOO_VERSION/templates/jupyterhub-builder.json

oc process templates/jupyterhub-builder \
    --param JUPYTERHUB_NAME=hbp-jupyterhub \
    --param GIT_REPOSITORY_URL=https://github.com/HumanBrainProject/clb-s2i-jupyterhub \
    --param GIT_REFERENCE=${CLB_HUB_VERSION} \
    | oc apply -f-

oc apply -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/$JOO_VERSION/templates/jupyterhub-deployer.json
oc process templates/jupyterhub-deployer \
    --param JUPYTERHUB_IMAGE=hbp-jupyterhub:${CLB_HUB_VERSION} \
    --param JUPYTERHUB_CONFIG="`cat jupyterhub_config.py`" \
    --param JUPYTERHUB_ENVVARS="$(cat jupyterhub_envvars_${CLB_ENV}.sh)" \
    --param NOTEBOOK_IMAGE=clb-jupyter-nb-base:${CLB_NB_VERSION} \
    --param NOTEBOOK_MEMORY=2Gi \
    | oc apply -f-

oc process -f templates/clb-notebook-base.yaml  |oc apply -f-
```


Would be nice, but needs modifications of the jupyterhub-deployer template to mount the secrets. Set in the env file for now.
```
oc create secret generic jupyterhub --from-literal=jupyterhub_crypt_key=$(openssl rand -hex 32  | tr -d '\n')
oc create secret generic oauth --from-literal=client_secret=<OAuth client secret>
```

```
oc create -f security_context_constraints/mounter.yaml
APPNAME=???
oc adm policy add-scc-to-user scc-mounter system:serviceaccount:$APPNAME:jupyterhub-hub
```

## Updating the clb notebook image

```
export CLB_NB_VERSION=v0.3.5-openshift
oc process templates/clb-nb-base --param BUILDER_IMAGE_GIT_REFERENCE=${CLB_NB_VERSION} BUILDER_NEURO_IMAGE_GIT_REFERENCE=${CLB_NB_VERSION} --param BASE_IMAGE_GIT_REFERENCE=${CLB_NB_VERSION} |oc apply -f-
oc start-build clb-jupyter-nb-builder

# @TODO is there a way to only change one parameter?
oc process templates/jupyterhub-deployer \
    --param JUPYTERHUB_IMAGE=hbp-jupyterhub:${CLB_HUB_VERSION} \
    --param JUPYTERHUB_CONFIG="`cat jupyterhub_config.py`" \
    --param JUPYTERHUB_ENVVARS="$(cat jupyterhub_envvars_${CLB_ENV}.sh)" \
    --param NOTEBOOK_IMAGE=clb-jupyter-nb-base:${CLB_NB_VERSION} \
    --param NOTEBOOK_MEMORY=2Gi \
    | oc apply -f-
```

## TODO

- [ ] Publish seahub patches
- [ ] Describe KeyCloak setup

## Tricks

Add to envvars to run db upgrade:
```
jupyterhub upgrade-db -f /opt/app-root/etc/jupyterhub_config.py
```
