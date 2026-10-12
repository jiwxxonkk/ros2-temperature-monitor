# HW2: ROS 2 Temperature Monitoring and Alert System

A ROS 2 temperature and humidity monitoring system developed for the **Operating System Practice** course. It uses custom messages and a service to publish simulated sensor readings, display temperature alerts, and update the temperature threshold at runtime.

The implementation follows the revised HW2 assignment specification and the provided starter template. The locally installed ROS 2 distribution is **Jazzy**.

## Repository Structure

The repository root is `~/hw2_ws/src`.

```text
src/
├── README.md
├── .gitignore
├── mysensor_interfaces/
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── msg/
│   │   ├── MyTime.msg
│   │   └── MySensorMsg.msg
│   └── srv/SetThreshold.srv
└── sensor_monitor_py/
    ├── package.xml
    ├── setup.py
    ├── setup.cfg
    ├── resource/sensor_monitor_py
    ├── launch/sensor_system.launch.py
    ├── test/
    └── sensor_monitor_py/
        ├── __init__.py
        ├── temperature_publisher.py
        ├── monitor_node.py
        └── threshold_client.py
```

Build artifacts (`build/`, `install/`, and `log/`) and Python caches are excluded from version control. The empty `resource/sensor_monitor_py` and `__init__.py` files are part of the package structure and should be retained.

## Nodes and Communication

| Node | Function |
|---|---|
| `temperature_publisher` | Publishes sensor readings to `/sensor_data` every second |
| `monitor_node` | Subscribes to sensor readings, logs INFO/WARN messages, and provides the `/set_threshold` service |
| `threshold_client` | Validates CLI arguments, sends one asynchronous threshold update request, and exits after receiving the response |

```text
temperature_publisher ── /sensor_data ──▶ monitor_node
threshold_client ──── /set_threshold ──▶ monitor_node
                 ◀── success response ──
```

### Custom Interfaces

`mysensor_interfaces/msg/MyTime.msg`

```text
int32 sec
int32 nsec
```

`mysensor_interfaces/msg/MySensorMsg.msg`

```text
float64 temp
float64 humidity
string sensor_id
MyTime stamp
```

`mysensor_interfaces/srv/SetThreshold.srv`

```text
float64 new_threshold
---
bool success
```

## Implementation Details

### Sensor Publisher

`TemperaturePublisher.timer_callback()` uses `random.uniform()` to generate temperatures between -10.0 and 50.0°C and relative humidity values between 10.0 and 99.0%. It calculates elapsed time from the current ROS clock and `self.t0`, which is stored during initialization. Integer division and modulo split the elapsed nanoseconds into `stamp.sec` and `stamp.nsec`.

```python
sec = total_nanoseconds // 1_000_000_000
nsec = total_nanoseconds % 1_000_000_000
```

`stamp` represents elapsed time since publisher initialization. The implementation assumes `use_sim_time=False` and no system clock changes during execution. The nanosecond component satisfies `0 <= nsec < 1,000,000,000`.

The sensor ID is read from a parameter at startup and remains fixed. Its default value is `sensor_01` when the node runs individually; the provided launch file sets it to `sensor_A`.

### Monitoring and Threshold Updates

`MonitorNode.sensor_callback()` logs the sensor ID, temperature, humidity, elapsed time, and current threshold once per received message. The nanosecond component is displayed with nine digits.

- Initial threshold: 30.0°C
- `temp < threshold`: INFO
- `temp >= threshold`: WARN
- Humidity is included in the log but does not affect the alert decision.

`threshold_callback()` uses `math.isfinite()` and a range check to validate requests. A finite value between -10.0 and 50.0, inclusive, updates `self.threshold` in the same monitor instance and returns `success=True`. Out-of-range values, NaN, and positive or negative infinity leave the existing threshold unchanged and return `success=False`.

### Client Input Handling

`parse_threshold()` checks that exactly one argument remains after removing ROS options and that it can be converted with `float()`. Invalid arguments produce a WARN message and cause the client to exit without waiting for the service. Values such as `nan`, `inf`, and out-of-range numbers are sent to the server for final validation.

`send_request()` returns the Future created by `call_async()`. After the response arrives, `log_response()` logs INFO for success or WARN for failure. If a valid numeric argument is supplied while the monitor is not running, the client waits for the service to become available.

## Build

ROS 2 Jazzy, colcon, and the ROS interface generation tools must be installed. Place both packages directly under `~/hw2_ws/src/`.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/hw2_ws
colcon build --symlink-install --packages-up-to sensor_monitor_py
source install/setup.bash

ros2 interface show mysensor_interfaces/msg/MyTime
ros2 interface show mysensor_interfaces/msg/MySensorMsg
ros2 interface show mysensor_interfaces/srv/SetThreshold
ros2 pkg executables sensor_monitor_py
```

If you use another ROS 2 distribution, adjust the setup path to match your environment.

## Run

Load the environment in every new terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/hw2_ws/install/setup.bash
```

Start the monitor in terminal A:

```bash
ros2 run sensor_monitor_py monitor_node
```

Start the publisher in terminal B:

```bash
ros2 run sensor_monitor_py temperature_publisher
```

Update the threshold in terminal C:

```bash
ros2 run sensor_monitor_py threshold_client 35.0
```

Alternatively, start both the monitor and publisher with the launch file. Do not run the individual nodes and the launch file simultaneously. Run the client separately when needed.

```bash
ros2 launch sensor_monitor_py sensor_system.launch.py
```

To specify a sensor ID when running the publisher individually:

```bash
ros2 run sensor_monitor_py temperature_publisher --ros-args -p sensor_id:=sensor_A
```

## Verification Procedure

The tables below describe **expected results**, not recorded execution results. The source code was compared with the assignment specification when preparing this README; live ROS communication was not revalidated during that review.

### Publication Rate and Elapsed Time

With the publisher and monitor running, execute the following commands in a separate terminal. Stop each command with Ctrl+C.

```bash
ros2 topic echo /sensor_data
ros2 topic hz /sensor_data
```

Check for approximately 1 Hz publication, the required temperature and humidity ranges, a fixed sensor ID, increasing elapsed time, and a valid `nsec` range.

### Alert Boundaries

Stop the publisher and run only one monitor. If using the launch file, stop it and restart only `monitor_node`.

```bash
ros2 run sensor_monitor_py threshold_client 30.0
ros2 topic pub --once /sensor_data mysensor_interfaces/msg/MySensorMsg \
  "{temp: 30.0, humidity: 50.0, sensor_id: 'test_sensor', stamp: {sec: 1, nsec: 0}}"
```

Repeat the test with the temperature and threshold values below:

| Threshold | Input Temperature | Expected Log |
|---|---|---|
| 30.0 | 29.9 | INFO |
| 30.0 | 30.0 | WARN |
| 30.0 | 30.1 | WARN |
| 30.0 | 32.0 | WARN |
| After updating to 35.0 | 32.0 | INFO |

### Invalid Thresholds and Arguments

Set the threshold to 35.0, then send invalid requests:

```bash
ros2 run sensor_monitor_py threshold_client 35.0
ros2 run sensor_monitor_py threshold_client 51.0
ros2 run sensor_monitor_py threshold_client -10.1
ros2 run sensor_monitor_py threshold_client nan
ros2 run sensor_monitor_py threshold_client inf
ros2 run sensor_monitor_py threshold_client -inf
```

Each invalid request should return `success=False` and produce a client WARN message. After each failed request, publish a temperature of 32.0 and check for INFO to verify that the threshold remains 35.0. Requests for -10.0 and 50.0 should succeed.

Stop the monitor, then check that the following commands print WARN and exit without waiting for the service:

```bash
ros2 run sensor_monitor_py threshold_client abc
ros2 run sensor_monitor_py threshold_client
ros2 run sensor_monitor_py threshold_client 30.0 35.0
```

Keep random sensor generation enabled in the submitted publisher. Record actual execution screenshots and verification results separately.
