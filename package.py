name = 'vetala'

# NOTE: This is actually coming from the latest "main" branch that was a little
# more updated than the actual tag 0.6.15
version = '0.6.15.sse.1.0.0'

authors = [
    'Louis Vottero',
]

description = '''Rig builder'''

with scope('config') as c:
    import os
    c.release_packages_path = os.environ['SSE_REZ_REPO_RELEASE_EXT']

requires = [
    "maya",
]

private_build_requires = [
]

variants = [
]

build_command = 'rez python {root}/rez_build.py'
uuid = 'repository.vtool'


def commands():
    # NOTE: REZ package versions can have ".sse." to separate the external
    # version from the internal modification version.
    split_versions = str(version).split(".sse.")
    external_version = split_versions[0]
    internal_version = None
    if len(split_versions) == 2:
        internal_version = split_versions[1]

    env.VETALA_VERSION = external_version
    env.VETALA_PACKAGE_VERSION = external_version
    if internal_version:
        env.VETALA_PACKAGE_VERSION = internal_version

    env.REZ_VETALA_ROOT = '{root}'
    env.PYTHONPATH.append('{root}/python')
