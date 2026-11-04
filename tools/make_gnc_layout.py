#!/usr/bin/env python3
"""Build lichtblick_layout_gnc2027.json from the simulation layout, using GNC-2027 topic names.

Only topics with a producer in TAMU-Lunabotics/GNC-2027 (see gnc2027_topics.txt) are used. Panels
with no GNC source (LiDAR scan, camera image, data-origin label) are removed or marked as having
no topic, never pointed at invented topics.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICHTBLICK = ROOT/'02_Ground_Station_Telemetry/deliverables/lichtblick'
TITLE = 'lichtblickPanelTitle'
GREY, GREEN, BLUE, AMBER, RED = '#616161', '#2e7d32', '#1565c0', '#f9a825', '#c62828'

HEALTH_SCRIPT = '''// {what} freshness for the operator display (display only: nothing is sent to ROS).
// /tf is used only as a heartbeat so a {what} topic that stops is reported as STALE.
// {limit_note}

export const inputs = ["{topic}", "/tf"];
export const output = "/studio_script/{name}";

type Time = {{ sec: number; nsec: number }};
type InputEvent = {{ topic: string; receiveTime: Time; message: any }};

type Health = {{
  {field}: string;
  {field}_age_s: number;
}};

const STALE_S = {limit};

let lastTime: number | undefined = undefined;

function seconds(t: Time): number {{
  return t.sec + t.nsec * 1e-9;
}}

export default function script(event: InputEvent): Health | undefined {{
  const now = seconds(event.receiveTime);
  if (event.topic === "{topic}") {{
    lastTime = now;
  }}
  if (lastTime === undefined) {{
    return {{ {field}: "NO_DATA", {field}_age_s: -1 }};
  }}
  if (now < lastTime) {{
    // Playback was moved backwards; wait for the next message.
    lastTime = undefined;
    return {{ {field}: "NO_DATA", {field}_age_s: -1 }};
  }}
  const age = now - lastTime;
  return {{ {field}: age <= STALE_S ? "OK" : "STALE", {field}_age_s: age }};
}}
'''

FOOTPRINT_SCRIPT = '''// Rover footprint for the 3D panel (display only: nothing is sent to ROS).
// Box attached to base_link, driven by /odometry/filtered. Size from GNC-2027
// luna_description/config/robot_geometry.yaml (1.0 x 0.7 x 0.4 m, marked ASSUMPTION there).

import { Message } from "./types";
import { buildRosMarker, MarkerTypes } from "./markers";

export const inputs = ["/odometry/filtered"];
export const output = "/studio_script/gnc_footprint";

type Time = { sec: number; nsec: number };
type InputEvent = { topic: string; receiveTime: Time; message: any };
type Marker = Message<"visualization_msgs/Marker">;

export default function script(event: InputEvent): Marker {
  return buildRosMarker({
    header: { frame_id: "base_link", stamp: event.receiveTime, seq: 0 },
    ns: "gnc_rover_footprint",
    id: 0,
    type: MarkerTypes.CUBE,
    action: 0,
    frame_locked: true,
    pose: {
      position: { x: 0, y: 0, z: 0.35 },
      orientation: { x: 0, y: 0, z: 0, w: 1 },
    },
    scale: { x: 1.0, y: 0.7, z: 0.4 },
    color: { r: 1.0, g: 0.6, b: 0.0, a: 0.6 },
  });
}
'''


def rule(value, color, label):
    return {'operator': '=', 'rawValue': value, 'color': color, 'label': label}


def split(direction, first, second, pct):
    return {'direction': direction, 'first': first, 'second': second, 'splitPercentage': pct}


def main():
    sim = json.loads((LICHTBLICK/'lichtblick_layout.json').read_text())
    c = {pid: copy.deepcopy(cfg) for pid, cfg in sim['configById'].items()
         if pid in ('3D!scene', 'Image!camera', 'Plot!motion', 'Plot!data_age', 'StateTransitions!timeline',
                    'SourceInfo!connection', 'SourceInfo!source', 'RawMessagesVirtual!status')}

    c['Indicator!guidance'] = {
        TITLE: 'GUIDANCE STATE (/guidance/status)', 'path': '/guidance/status.state', 'style': 'background',
        'rules': [rule('0', GREY, 'IDLE: no path'), rule('1', GREEN, 'FOLLOWING PATH'),
                  rule('2', BLUE, 'GOAL REACHED'), rule('3', RED, 'STOPPED: see Details (message)')],
        'fallbackColor': GREY, 'fallbackLabel': 'UNAVAILABLE: no /guidance/status'}
    c['Indicator!planner'] = {
        TITLE: 'PLANNER STATE (/planning/status)', 'path': '/planning/status.state', 'style': 'background',
        'rules': [rule('0', GREY, 'IDLE: no goal'), rule('1', AMBER, 'PLANNING'),
                  rule('2', GREEN, 'PATH PLANNED'), rule('3', RED, 'NO PATH: planner FAILED (see Details)')],
        'fallbackColor': GREY, 'fallbackLabel': 'UNAVAILABLE: no /planning/status'}

    def health(pid, title, path, name):
        c[pid] = {TITLE: title, 'path': path, 'style': 'bulb', 'fallbackColor': GREY,
                  'fallbackLabel': f'{name} UNAVAILABLE',
                  'rules': [rule('OK', GREEN, f'{name} OK'), rule('STALE', RED, f'{name} STALE'),
                            rule('NO_DATA', GREY, f'{name} NO DATA')]}
    health('Indicator!pose', 'Pose /odometry/filtered', '/studio_script/pose_health.pose', 'Pose')
    health('Indicator!imu', 'IMU /imu/data_raw', '/studio_script/imu_health.imu', 'IMU')

    scene = c['3D!scene']
    scene[TITLE] = 'Map, planned path, guidance (GNC-2027 topics)'
    scene['followTf'] = 'map'
    # GNC arena (artemis_arena.yaml): 6.88 x 5.0 m with the origin at a corner, +x along the length.
    scene['cameraState'].update({'targetOffset': [3.44, 2.5, 0], 'distance': 6.5})
    scene['layers']['arena-grid'].update({'frameId': 'map', 'size': 7, 'divisions': 7,
                                          'position': [3.44, 2.5, 0]})
    scene['transforms'] = {'frame:map': {'visible': True}, 'frame:base_link': {'visible': True}}
    grid = scene['topics'].pop('/sim/obstacle_grid')
    path = scene['topics'].pop('/sim/planned_path')
    scene['topics'] = {
        '/map': grid,
        '/guidance/path': path,
        '/guidance/collision_arc': {'visible': True, 'type': 'line', 'lineWidth': 0.04,
                                    'gradient': ['#ffab00ff', '#ffab00ff']},
        '/tags/markers': {'visible': True},
        '/studio_script/gnc_footprint': {'visible': True},
    }

    camera = c['Image!camera']
    camera[TITLE] = 'Camera: no image topic in GNC-2027 (CDH camera topic TBD)'
    camera['imageMode'] = {}

    c['Plot!motion'][TITLE] = 'Commanded speed (/cmd_vel TwistStamped from guidance)'
    c['Plot!motion']['paths'] = [
        {'value': '/cmd_vel.twist.linear.x', 'enabled': True, 'timestampMethod': 'receiveTime', 'label': 'linear.x (m/s)'},
        {'value': '/cmd_vel.twist.angular.z', 'enabled': True, 'timestampMethod': 'receiveTime', 'label': 'angular.z (rad/s)'}]
    c['Plot!data_age'][TITLE] = 'Data age (s): pose and IMU, limit 0.5 s'
    c['Plot!data_age']['paths'] = [
        {'value': '/studio_script/pose_health.pose_age_s', 'enabled': True, 'timestampMethod': 'receiveTime', 'label': 'pose'},
        {'value': '/studio_script/imu_health.imu_age_s', 'enabled': True, 'timestampMethod': 'receiveTime', 'label': 'IMU'}]
    c['Plot!tracking'] = {
        TITLE: 'Guidance tracking (m)', 'paths': [
            {'value': '/guidance/status.cross_track_error_m', 'enabled': True, 'timestampMethod': 'receiveTime', 'label': 'cross-track error'},
            {'value': '/guidance/status.distance_to_goal_m', 'enabled': True, 'timestampMethod': 'receiveTime', 'label': 'distance to goal'}],
        'xAxisVal': 'timestamp', 'showLegend': False, 'legendDisplay': 'floating', 'isSynced': True,
        'showXAxisLabels': True, 'showYAxisLabels': True}
    c['StateTransitions!timeline'][TITLE] = 'Guidance and planner state over time'
    c['StateTransitions!timeline']['paths'] = [
        {'value': '/guidance/status.state', 'label': 'Guidance', 'enabled': True, 'timestampMethod': 'receiveTime'},
        {'value': '/planning/status.state', 'label': 'Planner', 'enabled': True, 'timestampMethod': 'receiveTime'}]

    raw = c.pop('RawMessagesVirtual!status')
    c['RawMessagesVirtual!planner'] = raw | {TITLE: 'Raw /planning/status (reason in .message)',
                                            'topicPath': '/planning/status', 'diffTopicPath': '/planning/status'}
    c['RawMessagesVirtual!guidance'] = raw | {TITLE: 'Raw /guidance/status (reason in .message)',
                                             'topicPath': '/guidance/status', 'diffTopicPath': '/guidance/status'}

    operator = split('column',
        split('row', 'Indicator!guidance', 'Indicator!planner', 50),
        split('column',
            split('row', 'SourceInfo!connection', split('row', 'Indicator!pose', 'Indicator!imu', 50), 34),
            split('column',
                split('row', '3D!scene', 'Image!camera', 70),
                split('row', 'StateTransitions!timeline',
                      split('row', 'Plot!tracking', split('row', 'Plot!data_age', 'Plot!motion', 50), 34), 28),
                74),
            11),
        11)
    details = split('row', split('column', 'RawMessagesVirtual!planner', 'RawMessagesVirtual!guidance', 50),
                    'SourceInfo!source', 60)
    c['Tab!main'] = {'activeTabIdx': 0, 'tabs': [
        {'title': 'Operator (GNC-2027)', 'layout': operator},
        {'title': 'Details (raw status, source)', 'layout': details}]}

    scripts = {
        'gnc-pose_health': {'name': 'pose_health', 'sourceCode': HEALTH_SCRIPT.format(
            what='Pose', topic='/odometry/filtered', name='pose_health', field='pose', limit=0.5,
            limit_note='0.5 s matches the GNC-2027 path planner pose timeout.')},
        'gnc-imu_health': {'name': 'imu_health', 'sourceCode': HEALTH_SCRIPT.format(
            what='IMU', topic='/imu/data_raw', name='imu_health', field='imu', limit=0.5,
            limit_note='0.5 s is a display choice; GNC-2027 defines no IMU timeout yet.')},
        'gnc-footprint': {'name': 'gnc_footprint', 'sourceCode': FOOTPRINT_SCRIPT},
    }
    layout = {'configById': c, 'globalVariables': {}, 'userNodes': scripts,
              'playbackConfig': {'speed': 1}, 'layout': 'Tab!main'}
    out = LICHTBLICK/'lichtblick_layout_gnc2027.json'
    out.write_text(json.dumps(layout, indent=2)+'\n')
    print('wrote', out)


if __name__ == '__main__':
    main()
