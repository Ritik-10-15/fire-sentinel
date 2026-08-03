// Auto-generated Decision Tree inference function.
// Paste this into firesentinel_firmware.ino
int predictFireStatus(float flame_value, float smoke_ppm, float temperature_c, float humidity_pct) {
  if (flame_value <= 1350.15) {
    return 2;  // 0=Normal 1=Warning 2=Fire
  } else {
    if (smoke_ppm <= 297.80) {
      return 0;  // 0=Normal 1=Warning 2=Fire
    } else {
      if (flame_value <= 3270.85) {
        return 1;  // 0=Normal 1=Warning 2=Fire
      } else {
        return 0;  // 0=Normal 1=Warning 2=Fire
      }
    }
  }
}
