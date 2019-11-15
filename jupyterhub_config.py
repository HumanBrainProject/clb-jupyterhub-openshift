import os

c.JupyterHub.authenticator_class = 'clb_authenticator.ClbAuthenticator'
c.Authenticator.enable_auth_state = True
c.Authenticator.scope = ['email', 'roles', 'team', 'offline_access']

del c.KubeSpawner.cmd

c.KuJuDriveSpawner.http_timeout = 120
c.KuJuDriveSpawner.drive_url = os.environ.get('DRIVE_URL')
c.KuJuDriveSpawner.seadrive_sidecar_image = os.environ.get('SEADRIVE_SIDECAR_IMAGE')

c.KuJuDriveSpawner.extra_containers = [{
    "name": "seadrive-sidecar",
    "image": c.KuJuDriveSpawner.seadrive_sidecar_image,
    "securityContext": {
        "privileged": True,
        "capabilities": {
            "add": ["SYS_ADMIN"],
        },
    },
    "lifecycle": {
        "preStop": {
            "exec": {
                "command": ["fusermount", "-uz", "/mnt/share/drive"],
            },
        },
    },
    "volumeMounts": [
        {
            "name": "mnt-{username}",
            "mountPath": "/mnt/share",
            "mountPropagation": "Bidirectional",
        },
        {
            "name": "seadrive-{username}-conf",
            "mountPath": "/mnt/secrets/",
            "readOnly": True,
        },
    ],
}]

c.KuJuDriveSpawner.volumes = [
    {
        "name": "mnt-{username}",
        "emptyDir": {},
    },
    {
        "name": "seadrive-{username}-conf",
        "secret":
        {
            "secretName": "seadrive-{username}-conf",
        },
    },
]
c.KuJuDriveSpawner.volume_mounts = [{
    "name": "mnt-{username}",
    "mountPath": "/mnt/user",
    "mountPropagation": "HostToContainer",
}]

c.JupyterHub.spawner_class = 'kujudrivespawner.KuJuDriveSpawner'

# Kill user pods after 12 hours of inactivity.
c.JupyterHub.services = [
    {
        'name': 'cull-idle',
        'admin': True,
        'command': ['cull-idle-servers', '--timeout=86400'],
    }
]
