if [[ $PY311 == 1 ]]
then
    mkdir -p ./pydoc
    touch ./pydoc/__init__.py
    cat <<EOF > ./pydoc/__init__.py
def get_doc(*args):
    return ''
EOF
    mkdir -p ./webbrowser
    touch ./webbrowser/__init__.py
    cat <<EOF > ./webbrowser/__init__.py
EOF
    git clone https://${SECRET_TOKEN}@github.com/fusion-e/fusion-common.git
    pushd fusion-common && git checkout rel/magicp1-2.0.0 && popd
    git clone https://${SECRET_TOKEN}@github.com/fusion-e/fusion-manager.git
    pushd fusion-manager && git checkout rel/magicp1-2.0.0 && popd
    git clone https://${SECRET_TOKEN}@github.com/fusion-e/fusion-agent.git
    pushd fusion-agent && git checkout rel/magicp1-2.0.0 && popd
    git clone https://github.com/cloudify-incubator/cloudify-utilities-plugins-sdk.git
    pushd cloudify-utilities-plugins-sdk && git checkout fusion && popd
fi
