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

```
JOO_VERSION=3.2.2
DRIVE_URL=$(/bin/false) # DRIVE_URL
# dev projects only, builds should be re-used in production.
oc apply -f image-streams/jupyterhub.json
oc apply -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/$JOO_VERSION/templates/jupyterhub-builder.json \
    --param JUPYTERHUB_NAME=hbp-jupyterhub --param GIT_REPOSITORY_URL=https://github.com/HumanBrainProject/clb-s2i-jupyterhub
# prod and dev
oc apply -f https://raw.githubusercontent.com/HumanBrainProject/clb-jupyterhub-openshift/master/templates/jupyterhub-deployer.json
```

Setup the templates for the notebooks and sidecar

```
# dev projects only, builds should be re-used in production.

```

```
oc create secret generic jupyterhub --from-literal=jupyterhub_crypt_key=$(openssl rand -hex 32  | tr -d '\n')
oc create secret generic oauth --from-literal=client_secret=<OAuth client secret>
```

```
oc create -f security_context_constraints/mounter.yaml
```

```
oc new-app --template jupyterhub-deployer \
    --param-file=config/oauth.env -f templates/jupyterhub-deployer.json --param JUPYTERHUB_IMAGE=hbp-jupyterhub:latest \
    --param JUPYTERHUB_CONFIG="`cat jupyterhub_config.py`" --param SEADRIVE_SIDECAR_IMAGE=docker.io/villemai/seadrive-sidecar:v0.0.8 \
    --param DRIVE_URL=$DRIVE_URL --param NOTEBOOK_IMAGE=clb-jupyter-nb-base:latest --param NOTEBOOK_MEMORY=2Gi
oc adm policy add-scc-to-user scc-mounter system:serviceaccount:$APPNAME:jupyterhub-hub
```

## TODO

- [ ] Publish seahub patches
- [ ] Describe KeyCloak setup
