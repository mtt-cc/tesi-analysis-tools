#!/bin/bash

timeout 10 bash -c 'kubectl get crd | grep liqo | awk "{print \$1}" | xargs kubectl delete crd'

kubectl get crd | grep liqo | awk '{print $1}' | while read -r crd; do
    kubectl patch crd "$crd" -p '{"metadata":{"finalizers":[]}}' --type=merge
done

kubectl delete svc --all -n liqo

kubectl delete deploy --all -n liqo

kubectl delete daemonset --all -n liqo

kubectl delete pod --all -n liqo

kubectl delete -n liqo cronjob.batch/liqo-telemetry

kubectl delete -n liqo job.batch/liqo-pre-delete

timeout 5 bash -c '
  kubectl get ns | grep liqo | awk "{print \$1}" | while read -r namespace; do
      kubectl delete namespace "$namespace"
  done
'

kubectl get ns | grep liqo | awk '{print $1}' | while read -r namespace; do
    kubectl get namespace "$namespace" -o json \
      | tr -d "\n" | sed "s/\"finalizers\": \[[^]]\+\]/\"finalizers\": []/" \
      | kubectl replace --raw "/api/v1/namespaces/$namespace/finalize" -f -
done

kubectl get clusterrole | grep liqo | awk '{print $1}' | xargs kubectl delete clusterrole

kubectl get clusterrolebinding | grep liqo | awk '{print $1}' | xargs kubectl delete clusterrolebinding

kubectl get mutatingwebhookconfiguration | grep liqo | awk '{print $1}' | xargs kubectl delete mutatingwebhookconfiguration

kubectl get validatingwebhookconfiguration | grep liqo | awk '{print $1}' | xargs kubectl delete validatingwebhookconfiguration