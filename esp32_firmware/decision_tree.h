// Auto-generated Decision Tree inference function.
// Paste this into firesentinel_firmware.ino
int predictFireStatus(float flame_value, float smoke_ppm, float temperature_c, float humidity_pct) {
  if (flame_value <= 1564.00) {
    if (temperature_c <= 34.99) {
      if (flame_value <= 836.47) {
        return 0;  // 0=Normal 1=Warning 2=Fire
      } else {
        return 1;  // 0=Normal 1=Warning 2=Fire
      }
    } else {
      if (smoke_ppm <= 695.80) {
        if (temperature_c <= 60.20) {
          return 1;  // 0=Normal 1=Warning 2=Fire
        } else {
          return 2;  // 0=Normal 1=Warning 2=Fire
        }
      } else {
        if (humidity_pct <= 51.06) {
          return 2;  // 0=Normal 1=Warning 2=Fire
        } else {
          return 1;  // 0=Normal 1=Warning 2=Fire
        }
      }
    }
  } else {
    if (flame_value <= 2929.90) {
      if (temperature_c <= 23.99) {
        return 0;  // 0=Normal 1=Warning 2=Fire
      } else {
        if (temperature_c <= 50.41) {
          return 1;  // 0=Normal 1=Warning 2=Fire
        } else {
          return 2;  // 0=Normal 1=Warning 2=Fire
        }
      }
    } else {
      if (temperature_c <= 32.43) {
        if (smoke_ppm <= 700.35) {
          return 0;  // 0=Normal 1=Warning 2=Fire
        } else {
          return 1;  // 0=Normal 1=Warning 2=Fire
        }
      } else {
        if (temperature_c <= 35.98) {
          return 1;  // 0=Normal 1=Warning 2=Fire
        } else {
          return 1;  // 0=Normal 1=Warning 2=Fire
        }
      }
    }
  }
}
