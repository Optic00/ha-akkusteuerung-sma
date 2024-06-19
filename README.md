**DISCLAMER: Alles auf eigene Gefahr! Ich übernehme keine Verantwortung für Schäden oder Probleme die hiermit entstehen.**

(work in progress, noch nicht vollständig!)

# Anleitung # 

Was macht das hier eigentlich?

Akkuladesteuerung über den SHM 2.0 (wenn das berüchtigte März 2024 Update drauf ist, womit der WR nicht direkt gesteurt werden)
Akkuladesteuerung über den WR selbst (wenn man die Updates früh genug deaktiviert hat)

Ein Part ist die Reine Akku Lade-/Entladesteuerung die man manuell auswählen kann, der andere Part die Opti-Automatik welche die Ladestärke auf 0.2C (oder einen gewünschte Ladestärke) begrenzt, den Akku morgens erstmal auf 50% lädt und dann pausiert bis die gewünschte Restproduktionsprognose erreicht ist. Dann wird der Akku bis 90% weiter mit 0.2C beladen, danach mit 1kW bis 100%.

**opti-automatik.yaml** - Hiermit wird über den SHM 2.0 und freigeschaltetem GGC der Akku mittels der weiteren Automation gezielt geladen, pausiert und zuende geladen mit 0.2C bzw. 1kW. 

**sma-stp-se-ggc-shm-akku-steuerung.yaml** Dies ist die Automation um den Zustand der Lade/Entlade/Pause Steuerung anhand des DropDown Helfers zu steuern. 

**sma-ggc-automation.yaml** - Braucht man um den GGC an den SHM zu schicken. Werte müssen von Decimal in Hexadecimal umgewandelt werden und dann die hex-decimal in zwei packs

- [0xabcd]
- [0xabcd]

**configuration.yaml** - Eintrag zum Wechselrichter ODER falls man durch das Update März 2024 einen GGC braucht den Part für den SHM 2.0. Beides zusammen ist nicht notwendig

Wer erstmal nur die reine Akkusteuerung möchte, braucht nur die "sma-se-akku-steuerung.yaml" als Automation anlegen und u.g. Helfer und Überschuss Akkuladung anlegen.

**ToDo:**
- Akku im Winter mindestens 1x die Woche automatisch auf 100% Laden
- Evtl. Ladegeschwindigkeit ab 95-98% auf 500 Watt begrenzen
- SBS Version
- HACS Version für die reine Akkusteuerung
- English Version of this?

Den eintrag aus der configuration.yaml bei Homeassistant in die gleichnamige einfügen. Der eine Sensor ist ein Dummy-Eintrag den die HA Modbus Integration scheinbar seit einem der letzten Updates benötigt.

Man benötigt einen Sensor der den möglichen Überschuss für den Akku berechnet und einen für den aktuellen Hausverbrauch. 

**Zum Beispiel für den möglichen Akku-Ladeüberschuss:**

    - unique_id: maximaler_ueberschuss_akkuladung
      device_class: power
      state_class: measurement
      name: Maximaler Ueberschuss fuer Akkuladung Watt
      unit_of_measurement: W
      state: "{{ (states('sensor.pv_generation_komplett_watt') | float) - (states('sensor.home_energy_usage_watt') | float) - (states('sensor.sn_xxxxxxx_metering_power_absorbed') | float) + ((states('sensor.goecharger_wallbox_hinten_p_all')  | float )* 1000)  }}"

**Zum Beispiel für den Hausverbrauch:**

    - unique_id: home_energy_usage_w
      device_class: power
      state_class: measurement
      name: Home Energy Usage Watt
      unit_of_measurement: W
      state: "{{ (states('sensor.sn_3017XXXXXX_metering_power_absorbed') | float) + (states('sensor.sn_3017XXXXXX_grid_power') | float) - (states('sensor.sn_3017XXXXXX_metering_power_supplied') | float)}}"

**Hier als Extra zwei Sensoren die Wirkungsgrad und Akku_Zyklen in HA trackien**

    - unique_id: byd_akku_wirkungsgrad_lade_entlade
      name: BYD Akku Wirkungsgrad Ladung und Entladung
      unit_of_measurement: factor
      state: "{{ ((states('sensor.sn_3017XXXXXX_battery_discharge_total') | float) / (states('sensor.sn_3017XXXXXX_battery_charge_total') | float) * 100) | round(2) }}"

    - unique_id: byd_akku_zyklen
      name: BYD Akku Zyklen
      unit_of_measurement: factor
      state: "{{ (((((states('sensor.sn_3017XXXXXX_battery_discharge_total') | float) + (states('sensor.sn_3017XXXXXX_battery_charge_total') | float)) / 100 ) * (states('sensor.sn_3017XXXXXX_battery_capacity_total')) | float) / (2*10.2) ) | round(1) }}"


dieser HA-Helfer zur Auswahl des Akku-Modus muss angelegt werden:

<img width="567" alt="image" src="https://github.com/Optic00/ha-smase-akkusteuerung/assets/20187253/19fdf3d8-f7ef-45d4-a5eb-36d821aeb237">

Dann noch einen Schalter **byd_opti_automatik** ob diese Ladeoptimerung überhaupt laufen darf anlegen:

Vier Input Numbers anlegen, Minimaler Wert 100, maximaler Wert 10000 (Watt) für:

input_number.byd_akkusteuerung_entladestaerke_soll und 
input_number.byd_akkusteuerung_ladestaerke_soll
input_number.byd_akkusteuerung_02c_ladestaerke

für den letzten z.B. 1-100kWh, dies steuert die Schwelle ab wann der Akku von 50% aufwärts geladen wird.

input_number.byd_akku_ab_welchem_restertrag_vollladen

<img width="500" alt="image" src="https://github.com/Optic00/ha-smase-akkusteuerung/assets/20187253/6a1ae098-817a-4029-b732-442eeee4ae6d">
