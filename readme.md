Con K3s installato, mettere le label ai nodi
```# Labels to add to the nodes
declare -A LABELS
LABELS["node-role.fluidos.eu/worker"]="true"
LABELS["node-role.fluidos.eu/resources"]="true"

# Label the node
echo "  - Labeling the node"
for LABEL_KEY in "${!LABELS[@]}"; do
    LABEL_VALUE=${LABELS[$LABEL_KEY]}
    kubectl label node "$NODE_NAME" "$LABEL_KEY=$LABEL_VALUE" --overwrite
    echo "Label $LABEL_KEY=$LABEL_VALUE set on node $NODE_NAME"
done
```
Download del consumer-values.yaml
```
curl -s -o consumer-values.yaml https://raw.githubusercontent.com/fluidos-project/node/main/quickstart/utils/consumer-values.yaml
```
In questo file c’è un errore, devi cambiare  la riga 146 da imageName: "ghcr.io/fluidos/network-manager" a imageName: "ghcr.io/fluidos-project/network-manager" . Senza questo non riesce a pullare l’immagine.
Fatto questo, devi dichiarare delle variabili per installare.
```# FLUIDOS
FLUIDOS_VERSION="0.1.0"
NODE_NAME=vm1
HOST_INTERFACE=ens18
NODE_IP=$(ip a | grep $HOST_INTERFACE | grep inet | awk '{print $2}' | cut -d '/' -f 1)
REAR_PORT=30000
# Network Manager
ENABLE_LOCAL_DISCOVERY=true
FIRST_OCTET=10
SECOND_OCTET=200
THIRD_OCTET=0
```
Mi raccomando cambia il NODE_NAME e soprattutto SECOND_OCTET, ad esempio su una metti 200 e sull’altra metti 201 altrimenti non va la discovery. Attenzione a questo perché ci ho perso 3 ore per capire il problema perché è veramente un dettaglio.
Btw, penso tu abbia già aggiunto la repo ad Helm, ma nel caso usa questo
```helm repo add fluidos https://fluidos-project.github.io/node/ 1>/dev/null
helm repo update 1>/dev/null
```
Per installare dai questo comando
```
helm upgrade --install node fluidos/node \
        -n fluidos --version "$FLUIDOS_VERSION" \
        --create-namespace -f consumer-values.yaml \
        --set networkManager.configMaps.nodeIdentity.ip="$NODE_IP" \
        --set rearController.service.gateway.nodePort.port="$REAR_PORT" \
        --set networkManager.config.enableLocalDiscovery="$ENABLE_LOCAL_DISCOVERY" \
        --set networkManager.config.address.firstOctet="$FIRST_OCTET" \
        --set networkManager.config.address.secondOctet="$SECOND_OCTET" \
        --set networkManager.config.address.thirdOctet="$THIRD_OCTET" \
        --wait \
        --debug \
        --v=2
```
Fatto questo, devi patchare la rete di multus per la discovery, dato che in proxmox le VM hanno ens18 come interfaccia e non eth0. Usa questi comandi che fanno tutto loro.
```# Export the YAML to a file
kubectl get network-attachment-definitions.k8s.cni.cncf.io macvlan-conf -n fluidos -o yaml > macvlan-conf.yaml

# Modify eth0 to ens18 in the file
sed -i 's/"master": "eth0"/"master": "ens18"/' macvlan-conf.yaml

# Apply the modified YAML back to the cluster
kubectl apply -f macvlan-conf.yaml
```
Per disinstallare invece
```helm delete node -n fluidos --debug --v=2 --wait
kubectl delete namespace fluidos
kubectl get crd | grep fluidos.eu | awk '{print $1}' | xargs kubectl delete crd
```
Per l’ultimo puoi anche non usarlo, tanto le CRD non danno problemi di solito.