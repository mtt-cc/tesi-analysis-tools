# notice that this runs the REMOTE helm chart, if you need the local modified version put the path to local chart

helm upgrade --install node fluidos/node \ 
        -n fluidos --version "0.1.0" \
        --create-namespace -f consumer-values.yaml \
        --set networkManager.configMaps.nodeIdentity.ip="192.168.11.102" \
        --set rearController.service.gateway.nodePort.port="30000" \
        --set networkManager.config.enableLocalDiscovery="true" \
        --set networkManager.config.address.firstOctet="10" \
        --set networkManager.config.address.secondOctet="200" \
        --set networkManager.config.address.thirdOctet="0" \
        --wait \
        --debug \
        --v=2 

# \
#         --set containerSecurityContext.capabilities.add[0]=NET_ADMIN

# helm upgrade --install node fluidos/node \
# -n fluidos --version "0.1.0" \
# --create-namespace -f consumer-values.yaml \
# --set networkManager.configMaps.nodeIdentity.ip="192.168.11.103" \
# --set rearController.service.gateway.nodePort.port="30000" \
# --set networkManager.config.enableLocalDiscovery="true" \
# --set networkManager.config.address.firstOctet="10" \
# --set networkManager.config.address.secondOctet="201" \
# --set networkManager.config.address.thirdOctet="0" \
# --wait \
# --debug \
# --v=2


 helm repo add fluidos https://fluidos-project.github.io/node/

# to check CR
kubectl get <myresource>

#to watch resource
watch -n 1 kubectl describe knownclusters.network.fluidos.eu knowncluster-c7s4zeavro -n fluidos

watch kubectl get knownclusters.network.fluidos.eu knowncluster-c7s4zeavro -n fluidos -o yaml
# set multicast
sudo ip link set dev ens18 multicast on

# disabilitare multicast non impedisce a networkmanager di funzionare 
#(a meno che il multicast non venga ricevuto su ens18 ma su un'altra interfaccia)
# alternative:
# k8 non permette di fermare momentaneamente un pod, ma si può fare in due modi:
# deployments/node/templates/fluidos-network-manager-daemonset.yaml
# 1) patchare daemonset con nuova label per farlo fermare e poi ripartire
# 2) modificare lo yaml con una nuova label e fare apply
name: {{ include "fluidos.prefixedName" $networkManagerConfig }} node-network-manager

# Add a non-existent node label to temporarily remove all DaemonSet Pods
kubectl patch daemonset node-network-manager -n fluidos \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/nodeSelector", "value": {"non-existent-label": "true"}}]'

# To resume, remove the nodeSelector or reset it to its original value
kubectl patch daemonset node-network-manager -n fluidos \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/nodeSelector", "value": {"node-role.fluidos.eu/worker": "true"}}]'

# watch
watch -n 1 kubectl describe knownclusters.network.fluidos.eu knowncluster-wqogimmzsq -n fluidos
# manually delete the resource
kubectl delete knownclusters.network.fluidos.eu -n fluidos knowncluster-wqogimmzsq


# NAMESPACE   LAST SEEN   TYPE     REASON             OBJECT                           MESSAGE
# fluidos     7s          Normal   AddedInterface     Pod/node-network-manager-trqdv   Add eth0 [10.42.0.43/24] from cbr0
# fluidos     7s          Normal   AddedInterface     Pod/node-network-manager-trqdv   Add eth1 [10.201.0.101/24] from fluidos/macvlan-conf
# what are these interfaces in the NetworkManager used for?

# why these inconsistency in the time it takes to find a node? 
# next step, setup automated testing to take average of 1000 runs
# consider that in this time we include the creation of the network manager
# and thus it is a fair simulation of launching fluidos on a new node
#--> the problem is in the inconsistency in launching the network manager pod, 
# how to isolate it? compute the time after the network manager running event is launched
# fluidos     12m         Normal   Started            pod/node-network-manager-gd86z   Started container network-manager

# i need privilege escalation within network-manager container to modify if links
deployments/node/templates/_helpers.tpl
# need to modify security config contained here

```
Get the Pod security context
*/}}
{{- define "fluidos.podSecurityContext" -}}
#runAsNonRoot: true
#runAsUser: 1000
#runAsGroup: 1000
#fsGroup: 1000
{{- end -}}

{{/*
Get the Container security context
*/}}
{{- define "fluidos.containerSecurityContext" -}}
runAsUser: 0       # Runs the container as the root user
runAsGroup: 0      # Runs the container as the root group
capabilities:
    add:
    - NET_ADMIN      # Grants the container permission to modify network interfaces
allowPrivilegeEscalation: true
{{- end -}}
```

# and also needed to modify chart version because for some reason it was pulling image :0.0.1 
# instead of :v0.1.0

# Since container restarts will reset the interface configuration, you can automate the multicast
# disablement by adding the ip command to the container's entrypoint or startup script.

# For example:

command: ["/bin/sh", "-c"]
        args:
          - |
            apk add --no-cache iproute2 &&
            /usr/bin/network-manager \
            --enable-local-discovery={{ .Values.networkManager.config.enableLocalDiscovery | toString }} \
            {{- if eq .Values.networkManager.config.enableLocalDiscovery true }}
            --cniInterface={{ (get .Values.networkManager.pod.annotations "k8s.v1.cni.cncf.io/networks" | split "@")._1 }} \
            {{- end }}

# disabling multicast still does not work since probably the forwarding from the host 
# interface removes the multicast layer and probably re encapsulates -> to be verified

kubectl exec -it node-network-manager-nlz2g -n fluidos -- sh

tc qdisc add dev eth1 root netem delay 250ms
tc qdisc add dev eth1 root netem loss 5%
tc qdisc show dev eth1
tc qdisc del dev eth1 root netem

# RECAP: to test with delay we need:
# -  use modified local helm chart with correct version
# - tag form image pull v0.1.0 in consumer-values.yaml
# - modify daemonset
# - modify _helpers.tpl to gain root access for container


# FOR PRESENTATION
# the answer is yes --> neuropil uses tapestry dht: overlay network based on ids obtained using hashing, bloom filters for efficient lookup

# Shift towards testing: what is more useful in which situation?

# Describe vm setup
# Development of benchmarking program using python k8s client and with attention to KnownCluster Resource

# Netem and packet loss: challenges in testing, modifying helm chart, multus setup

# about multus: the fact is that i dont have the understanding yet on how multus operates in our context
# --> could be very useful dont you think?

# now until 12: understand network config, if not understood remove from presentation
# how does my networking work?

# each pod has its own network namespace
# the cni creates a veth pair for each pod


# todo: tested with physical hardware
# should I do some work such that the benchmark is
# completely automated?
# right now on m2 you need to manually acces container
# and type commands, maybe write script to automate this?


# could it be that the results are so close because
# I always wait the same amount of time? what if i start
# exactly when the 


/usr/bin/python3 /app/k8s_main.py --node-bootstrap-address "*:udp4:192.168.11.102:2345"