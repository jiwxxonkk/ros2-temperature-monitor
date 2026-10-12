# HW2: ROS 2 온도 센서 및 경고 시스템

사용자 정의 메시지와 서비스를 이용한 ROS 2 센서 감시 과제입니다. 실제 센서 대신 난수로 온도·습도를 생성하고, 온도가 임계값 이상이면 경고를 출력합니다. 실행 중 서비스 요청으로 임계값을 변경할 수 있습니다.

`HW2_수정본.pdf`의 요구사항과 제공 템플릿을 바탕으로 구현했습니다. 로컬에 설치된 ROS 2 배포판은 **Jazzy**입니다.

## 구성

이 저장소는 `~/hw2_ws/src`를 루트로 사용합니다.

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

`build/`, `install/`, `log/` 및 Python 캐시는 버전 관리에서 제외합니다. 빈 `resource/sensor_monitor_py`와 `__init__.py`는 패키지 구성에 필요한 파일입니다.

## 노드와 통신

| 노드 | 구현 내용 |
|---|---|
| `temperature_publisher` | 1초마다 센서 데이터를 `/sensor_data`로 발행 |
| `monitor_node` | 센서 데이터를 구독해 INFO/WARN 출력, `/set_threshold` 서비스 제공 |
| `threshold_client` | CLI 인자를 검사하고 임계값 변경을 비동기로 1회 요청한 뒤 종료 |

```text
temperature_publisher ── /sensor_data ──▶ monitor_node
threshold_client ──── /set_threshold ──▶ monitor_node
                 ◀── success 응답 ─────
```

### 사용자 정의 인터페이스

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

## 구현 상세

### 센서 발행

`TemperaturePublisher.timer_callback()`에서 `random.uniform()`으로 온도 -10.0~50.0°C, 습도 10.0~99.0%를 생성합니다. 생성자에서 저장한 `self.t0`와 현재 ROS 시계의 차이를 나노초로 구하고, 정수 나눗셈과 나머지 연산으로 `stamp.sec`와 `stamp.nsec`를 채웁니다.

```python
sec = total_nanoseconds // 1_000_000_000
nsec = total_nanoseconds % 1_000_000_000
```

`stamp`는 publisher 초기화 이후 경과 시간입니다. `use_sim_time=False`이고 실행 중 시스템 시간이 변경되지 않는 환경을 가정합니다. `nsec`는 0 이상 1,000,000,000 미만입니다.

센서 ID는 시작할 때 파라미터에서 읽어 고정합니다. 단독 실행 기본값은 `sensor_01`, 제공 launch 파일의 설정값은 `sensor_A`입니다.

### 감시 및 임계값 변경

`MonitorNode.sensor_callback()`은 메시지마다 센서 ID, 온도, 습도, 경과 시간, 현재 임계값을 한 번 출력합니다. 시간의 나노초 부분은 9자리로 표시합니다.

- 초기 임계값: 30.0°C
- `temp < threshold`: INFO
- `temp >= threshold`: WARN
- 습도는 로그에만 표시하며 경고 판단에 사용하지 않습니다.

`threshold_callback()`은 `math.isfinite()`와 범위 검사를 수행합니다. -10.0~50.0 사이의 유한한 값이면 같은 monitor 인스턴스의 `self.threshold`를 갱신하고 `success=True`를 반환합니다. 범위 밖 값, NaN, 양·음의 무한대는 기존 임계값을 유지하고 `success=False`를 반환합니다. 양 끝값은 허용합니다.

### 클라이언트 입력 처리

`parse_threshold()`는 ROS 옵션을 제외한 인자가 정확히 하나인지, `float()`로 변환 가능한지 검사합니다. 잘못된 인자는 WARN 출력 후 서비스 준비를 기다리지 않고 종료합니다. 숫자로 변환 가능한 `nan`, `inf`, 범위 밖 값은 서버로 보내 최종 검증을 받습니다.

`send_request()`는 `call_async()`의 Future를 반환합니다. 응답을 기다린 후 `log_response()`가 성공은 INFO, 실패는 WARN으로 출력합니다. 유효한 숫자를 입력했으나 monitor가 실행되지 않았다면 서비스가 준비될 때까지 기다립니다.

## 빌드

ROS 2 Jazzy, colcon 및 ROS 인터페이스 생성 도구가 설치된 환경에서 실행합니다. 두 패키지는 `~/hw2_ws/src/` 바로 아래에 있어야 합니다.

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

다른 ROS 2 배포판을 사용한다면 setup 경로를 해당 환경에 맞게 변경합니다.

## 실행

모든 새 터미널에서 먼저 환경을 불러옵니다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/hw2_ws/install/setup.bash
```

터미널 A에서 감시 노드를 실행합니다.

```bash
ros2 run sensor_monitor_py monitor_node
```

터미널 B에서 센서 발행 노드를 실행합니다.

```bash
ros2 run sensor_monitor_py temperature_publisher
```

터미널 C에서 임계값을 변경합니다.

```bash
ros2 run sensor_monitor_py threshold_client 35.0
```

A와 B를 각각 실행하는 대신 아래 launch 명령으로 두 노드를 함께 시작할 수 있습니다. 개별 실행과 launch를 중복 실행하지 않습니다. 클라이언트는 별도 터미널에서 실행합니다.

```bash
ros2 launch sensor_monitor_py sensor_system.launch.py
```

단독 실행 시 센서 이름을 지정하려면 다음과 같이 실행합니다.

```bash
ros2 run sensor_monitor_py temperature_publisher --ros-args -p sensor_id:=sensor_A
```

## 동작 확인 절차

아래 표는 **기대 결과**이며 실제 실행 결과를 기록한 표는 아닙니다. 이 README 작성 시 소스와 과제 명세를 대조했으며 ROS 노드의 실시간 통신을 재검증하지는 않았습니다.

### 발행 주기와 경과 시간

publisher와 monitor가 실행 중일 때 별도 터미널에서 확인합니다. 각 명령은 Ctrl+C로 종료합니다.

```bash
ros2 topic echo /sensor_data
ros2 topic hz /sensor_data
```

약 1 Hz 발행, 지정된 온도·습도 범위, 고정 센서 ID, 증가하는 경과 시간과 `nsec` 범위를 확인합니다.

### 경고 경계값

publisher를 종료하고 monitor만 하나 실행합니다. launch를 사용했다면 종료한 뒤 monitor만 다시 실행합니다.

```bash
ros2 run sensor_monitor_py threshold_client 30.0
ros2 topic pub --once /sensor_data mysensor_interfaces/msg/MySensorMsg \
  "{temp: 30.0, humidity: 50.0, sensor_id: 'test_sensor', stamp: {sec: 1, nsec: 0}}"
```

위 명령의 온도와 클라이언트 인자를 변경하며 확인합니다.

| 임계값 | 입력 온도 | 기대 로그 |
|---|---|---|
| 30.0 | 29.9 | INFO |
| 30.0 | 30.0 | WARN |
| 30.0 | 30.1 | WARN |
| 30.0 | 32.0 | WARN |
| 35.0으로 변경 후 | 32.0 | INFO |

### 잘못된 임계값 및 입력

먼저 임계값을 35.0으로 설정하고 다음을 실행합니다.

```bash
ros2 run sensor_monitor_py threshold_client 35.0
ros2 run sensor_monitor_py threshold_client 51.0
ros2 run sensor_monitor_py threshold_client -10.1
ros2 run sensor_monitor_py threshold_client nan
ros2 run sensor_monitor_py threshold_client inf
ros2 run sensor_monitor_py threshold_client -inf
```

잘못된 요청은 모두 `success=False`에 따른 WARN이 기대됩니다. 각 실패 요청 직후 온도 32.0 메시지를 보내 INFO가 나오는지 확인하면 임계값 35.0의 유지 여부를 검사할 수 있습니다. -10.0 및 50.0 요청은 성공해야 합니다.

monitor를 종료한 뒤 다음 명령이 서비스 대기 없이 WARN을 출력하고 종료하는지도 확인합니다.

```bash
ros2 run sensor_monitor_py threshold_client abc
ros2 run sensor_monitor_py threshold_client
ros2 run sensor_monitor_py threshold_client 30.0 35.0
```

제출용 publisher는 난수 생성을 유지합니다. 실제 실행 화면과 검증 결과는 별도로 기록합니다.
