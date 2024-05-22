(work in progress, noch nicht vollständig!)

Wer erstmal nur die reine Akkusteuerung möchte, braucht nur die "sma-se-akku-steuerung.yaml" als Automation anlegen und u.g. Helfer und Überschuss Akkuladung anlegen.

ToDo:
- Akku im Winter mindestens 1x die Woche automatisch auf 100% Laden
- Evtl. Ladegeschwindigkeit ab 95-98% auf 500 Watt begrenzen
- Angabe der Akkukapazität zur Berechnung von 0.2C oder manuelle Eingabe von 0.2C
- SBS Version
- HACS Version für die reine Akkusteuerung
- English Version of this?

Den eintrag aus der configuration.yaml bei Homeassistant in die gleichnamige einfügen. Der eine Sensor ist ein Dummy-Eintrag den die HA Modbus Integration scheinbar seit einem der letzten Updates benötigt.

Man benötigt einen Sensor der den möglichen Überschuss für den Akku berechnet. 

    - unique_id: maximaler_ueberschuss_akkuladung
      device_class: power
      state_class: measurement
      name: Maximaler Ueberschuss fuer Akkuladung Watt
      unit_of_measurement: W
      state: "{{ (states('sensor.pv_generation_komplett_watt') | float) - (states('sensor.home_energy_usage_watt') | float) - (states('sensor.sn_xxxxxxx_metering_power_absorbed') | float) + ((states('sensor.goecharger_wallbox_hinten_p_all')  | float )* 1000)  }}"


dieser HA-Helfer zur Auswahl des Akku-Modus muss angelegt werden:

<img width="567" alt="image" src="https://github.com/Optic00/ha-smase-akkusteuerung/assets/20187253/19fdf3d8-f7ef-45d4-a5eb-36d821aeb237">

Dann noch einen Schalter ob diese Ladeoptimerung überhaupt laufen darf anlegen:

<img width="563" alt="image" src="https://github.com/Optic00/ha-smase-akkusteuerung/assets/20187253/b5939bc3-6930-4772-93df-3e0b47b6b0f3">

Zwei Input Numbers anlegen, Minimaler Wert 100, maximaler Wert 10000 (Watt):

input_number.byd_akkusteuerung_entladestaerke_soll und 
input_number.byd_akkusteuerung_ladestaerke_soll

<img width="500" alt="image" src="https://github.com/Optic00/ha-smase-akkusteuerung/assets/20187253/6a1ae098-817a-4029-b732-442eeee4ae6d">
