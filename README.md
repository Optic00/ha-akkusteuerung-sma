# Prognosebasierte & Manuelle Steuerung für Homeassistant von SMA STP SE Hybrid-Wechselrichter #

**DISCLAMER: Alles auf eigene Gefahr! Ich übernehme keine Verantwortung für Schäden oder Probleme die hiermit entstehen.**
Dieses Projekt wird in keinster Weise von der Firma SMA begleitet oder supported.

**Neue Betafirma seit 16.07.2024 stellt wieder die alte Funktionalität her, dass der Wechselrichter direkt über Modbus gesteurt werden kann**
Grid Guard Code usw. nicht mehr notwendig!

Noch kein Tibber? 50€ Bonus für mich & dich: https://invite.tibber.com/14sk9m15

(work in progress, noch nicht vollständig!)

# Anleitung # 

Was macht das hier eigentlich?

Akkuladesteuerung über den WR selbst (wenn man die Updates früh genug deaktiviert hat ODER die neue Betafirmware für den SHM 2.0 hat)

Ein Part ist die Reine Akku Lade-/Entladesteuerung die man manuell auswählen kann, der andere Part die Opti-Automatik welche die Ladestärke auf 0.2C (oder einen gewünschte Ladestärke) begrenzt, den Akku morgens erstmal auf 50% lädt und dann pausiert bis die gewünschte Restproduktionsprognose erreicht ist. Dann wird der Akku bis 90% weiter mit 0.2C beladen, danach mit 1kW bis 100%.

Es sollte die SMA Integration von HA eingerichtet werde um den SoC des Akkus auslesen zu können sowie ein Solcast Account für die Prognose der PV-Erträge!

**opti-automatik.yaml** - Hiermit wird über den SHM 2.0 und freigeschaltetem GGC der Akku mittels der weiteren Automation gezielt geladen, pausiert und zuende geladen mit 0.2C bzw. 1kW. 

**sma-se-akku-steuerung.yaml** - Falls man den WR noch direkt ansteuern kann und die letzten Updates nicht hat / die neue Beta Firmware (siehe oben) kann man diese Steuer-Automatik nutzen.

**configuration.yaml** - Eintrag zum Wechselrichter. Den Sensor für die Temperatur bitte mitnehmen, ohne Sensor funktioniert die Modbus Integration nicht zuverlässig.

Wer erstmal nur die reine Akkusteuerung möchte, braucht nur die "sma-se-akku-steuerung.yaml" als Automation anlegen und u.g. Helfer und Überschuss Akkuladung anlegen.

**ToDo:**
- Akku im Winter mindestens 1x die Woche automatisch auf 100% Laden
- Evtl. Ladegeschwindigkeit ab 95-98% auf 500 Watt begrenzen
- SBS Version
- HACS Version für die reine Akkusteuerung
- English Version of this?

Den Eintrag aus der configuration.yaml bei Homeassistant in die gleichnamige einfügen. 

Man benötigt einen Sensor der den möglichen Überschuss für den Akku berechnet und einen für den aktuellen Hausverbrauch. 

**Zum Beispiel für den möglichen Akku-Ladeüberschuss:**

    - unique_id: maximaler_ueberschuss_akkuladung
      device_class: power
      state_class: measurement
      name: Maximaler Ueberschuss fuer Akkuladung Watt
      unit_of_measurement: W
      state: "{{ (states('sensor.pv_generation_komplett_watt') | float) - (states('sensor.home_energy_usage_watt') | float) - (states('sensor.sn_xxxxxxx_metering_power_absorbed') | float) + ((states('sensor.goecharger_wallbox_hinten_p_all')  | float )* 1000)  }}"

**Zum Beispiel für den PV-Überschuss um ggf. die 70% Kappung zu erkennen**

    - unique_id: akkusteuerung_ueberschuss_pv
      device_class: power
      state_class: measurement
      name: Ueberschuss PV Watt
      unit_of_measurement: W
      state: "{{ (states('sensor.pv_generation_komplett_watt') | float(0) - (states('sensor.home_energy_usage_watt') | float) - (states('sensor.sn_3017XXXXXX_metering_power_absorbed') | float) )  }}"

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

Dann noch einen Schalter **akku_opti_automatik** ob diese Ladeoptimerung überhaupt laufen darf anlegen:

Vier Input Numbers anlegen, Minimaler Wert 100, maximaler Wert 10000 (Watt) für:

input_number.byd_akkusteuerung_entladestaerke_soll und 
input_number.byd_akkusteuerung_ladestaerke_soll
input_number.byd_akkusteuerung_02c_ladestaerke

für den letzten z.B. 1-100kWh, dies steuert die Schwelle ab wann der Akku von 50% aufwärts geladen wird.

input_number.byd_akku_ab_welchem_restertrag_vollladen

<img width="500" alt="image" src="https://github.com/Optic00/ha-smase-akkusteuerung/assets/20187253/6a1ae098-817a-4029-b732-442eeee4ae6d">
