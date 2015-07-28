#!/bin/sh

echo "# ------------------------------------------------------------------------------------------------------"
echo "# Extracting Key Performance Indicators (KPI) from metrics collected in data/logs/pmi_collect_allPMI.log"
echo "# ------------------------------------------------------------------------------------------------------"
echo

echo "# ------------------------------------------------------------------------------------------------------"
echo "# --- PKI for JVM: HeapSize, UsedMemory, FreeMemory"
echo "# ------------------------------------------------------------------------------------------------------"
grep -i heapsize data/logs/pmi_collect_all*
echo
grep -i usedmemory data/logs/pmi_collect_all*
echo
grep -i freememory data/logs/pmi_collect_all*
echo

echo "# ------------------------------------------------------------------------------------------------------"
echo "# --- PKI for Threads: ActiveCount, PoolSize, DeclaredThreadHungCount"
echo "# ------------------------------------------------------------------------------------------------------"
grep -i activecount data/logs/pmi_collect_all*
echo
grep -i poolsize data/logs/pmi_collect_all* | grep -i threadpool
echo
grep -i declaredthreadhungcount data/logs/pmi_collect_all*
echo

echo "# ------------------------------------------------------------------------------------------------------"
echo "# --- PKI for DB connections: PoolSize, FreePoolSize, UseTime, WaitingThreadCount, WaitTime, PercentUsed"
echo "# ------------------------------------------------------------------------------------------------------"
grep -i poolsize data/logs/pmi_collect_all* | grep -i jdbc
echo
grep -i freepoolsize data/logs/pmi_collect_all*
echo
grep -i usetime data/logs/pmi_collect_all*
echo
grep -i waitingthreadcount data/logs/pmi_collect_all*
echo
grep -i waittime data/logs/pmi_collect_all*
echo
grep -i percentused data/logs/pmi_collect_all*
echo

echo "# ------------------------------------------------------------------------------------------------------"
echo "# --- PKI for DB cache: PrepStmtCacheDiscardCount"
echo "# ------------------------------------------------------------------------------------------------------"
grep -i PrepStmtCacheDiscardCount data/logs/pmi_collect_all*
echo
