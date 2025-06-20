
# Firmware Update Log Rules & Heuristics

## 🔁 Firmware Update Execution Flow

During the firmware update, the following threads are involved:

- **Main Thread (`applySettingsExecutor`)**: Monitors the entire process.
- **Installset Thread (`installsetFingerPrintingQ`)**: Fetches server inventory and generates compliance data.
- **Staging Thread (`fwNANDStagingExecutor`)**: Stages components on the server repository.

The **main thread** also performs installation and determines whether the update succeeded or failed.

---

## ⚠️ Common Issue Patterns

### 🔹 Unexpected Problem During Power Cycle
- **UUID**: 34313750-3235-4D32-3238-323030365858
- **Bundle**: P76089_001_gen12spp-2024_09_00_00
- Threads: `applySettingsExecutor_1b10`, `installsetFingerPrintingQ_662`, `fwNANDStagingExecutor_1c39`

### 🔹 Installset Generation Failure
- **UUID**: 39343550-3635-444F-3236-505030303430
- **Bundle**: P73558_001_gen11spp-2024_04_00_00
- Threads: `applySettingsExecutor_671`, `installsetFingerPrintingQ_6aac`

### 🔹 Component Update Failure (`bcm228.1.111.0.pup.fwpkg`)
- **UUID**: 39333550-3132-4D33-3144-314831334A42
- Threads: `applySettingsExecutor_63b`, `installsetFingerPrintingQ_f48`, `fwNANDStagingExecutor_728`

### ✅ Successful Update Pattern
- **UUID**: 39333550-3132-4D33-3144-314831334A42
- Threads: `applySettingsExecutor_1999`, `installsetFingerPrintingQ_1293`, `fwNANDStagingExecutor_1ad5`

---

## 🛠️ Executors by Update Type

### Offline Firmware Update
- `applySettingsExecutor`
- `installsetFingerPrintingQ`
- `fwNANDStagingExecutor`

### Online Firmware Update (additional)
- `risEventActionExecutor`
- `sutStatusValidationExecutor`
- `sutStateValidationExecutor`

---

## 🧭 How to Identify Firmware Update Type

### For Gen10:

- **Offline Plugin**: `BareMetalActuatorFramework`
- **Online Plugin**: `RisFirmwareSettingsPlugin`

#### Sample Log (Offline)
```
[APPLY_SETTINGS] calling plugin#[8]:[BareMetalActuatorFramework] ...
```

#### Sample Log (Online)
```
[APPLY_SETTINGS] calling plugin#[11]:[RisFirmwareSettingsPlugin] ...
```

### For Gen11/Gen12:

- Plugin: `RedfishFirmwareUpdateActuatorPlugin`

To determine update type:
- If log mentions `RedfishOfflineFirmwareUpdatePlugin` as **not applicable** → it's **online**
- If not mentioned → it's **offline**

---

## 🗝️ Key Log Entries to Search

- **Start of update**: `[APPLY_SETTINGS] Begin Apply Settings`
- **Install status**: `"task queue details of the firmware update on server"`

---

## 📌 Identify Baseline Used

Search:
```
applySettingsExecutor_44d2, isBaselineAbsarokaCompliant():4187, The selected baseline SSPSY-... is absaroka compliant = true
```

---

## 📍 Gen10 Online Update Indicator

If this log is present:
```
[BareMetalActuatorFramework][apply] No settings need to be applied; End apply operation for the server.
```
→ Indicates **online** firmware update.

---

## ✅ Successful Offline Firmware Update (All Gens)

Check for both lines:
1. `fetchFailedComponentList ... 0`
2. `Absaroka Firmware update is complete for server: <UUID>`

### Example Logs (Offline Success)

#### Gen10
```
fetchFailedComponentList Total number of failed components ... 0  
Absaroka Firmware update is complete ...
```

#### Gen11/Gen12
```
fetchFailedComponentList Total number of failed components ... 0  
Absaroka Firmware update is complete ...
```

---

## ✅ Successful Online Firmware Update (All Gens)

Check for:
- `[ServerFirmwareUtil::fetchOverAllFirmwareInstallState] ... Activated`
- `Updating iLO with fwInstallState: Activated for server: <UUID>`

### ❌ Failure Indicators:
- Last occurrence of `fwInstallState` is:
  - `StageFailed`
  - `InstallFailed`
  - `ActivateFailed`
- OR log line is **missing entirely**

### Example Logs (Online Success)
```
[ServerFirmwareUtil::fetchOverAllFirmwareInstallState] Overall fwInstallState values is Activated  
Updating iLO with fwInstallState: Activated for server: ...
```

---

## 🧾 Alternative: Use installSetLogs.log

More reliable across all generations.

- **Location**: `/ci/logs/installSetLogs.log`
- **Look for**:  
  `"Received generateInstallSet request for the server = <UUID>"`

Check:
- `"update_type": "offline"`
- `"update_type": "online"`

---

## ❌ Failure Rules for Online Firmware Updates

1. Log **does not contain** `Updating iLO with fwInstallState:` → Failure  
2. Last value of that log **≠ Activated** → Failure
