#! /usr/bin/env python3

"""
Web Dashboard for ZlsNasDisplay

Provides a FastAPI-based web interface for remote monitoring of NAS metrics.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from zlsnasdisplay.network_operations import NetworkOperations, TrafficMonitor
from zlsnasdisplay.system_operations import SystemOperations


class MetricsCollector:
    """Collects all system metrics in a structured format."""

    def __init__(self, is_root: bool = False) -> None:
        self.is_root = is_root
        self.traffic_monitor = TrafficMonitor()
        self.system_ops = SystemOperations()
        self.network_ops = NetworkOperations()

    def get_all_metrics(self) -> dict[str, Any]:
        """Collect all system metrics and return as dictionary."""
        try:
            # Get traffic data
            traffic = self.traffic_monitor.get_current_traffic()

            # Collect all metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "load": self.system_ops.get_cpu_load(),
                    "temperature": self.system_ops.get_cpu_temperature(),
                },
                "memory": {"usage_percent": SystemOperations.get_mem()},
                "nvme": {
                    "usage_percent": SystemOperations.get_nvme_usage(),
                    "temperature": SystemOperations.get_nvme_temp(),
                },
                "fan": {"speed_rpm": SystemOperations.get_fan_speed()},
                "network": {
                    "ip_address": self.network_ops.get_ip_address(),
                    "signal_strength_dbm": self.network_ops.get_signal_strength(),
                    "internet_connected": self.network_ops.check_internet_connection(),
                    "traffic": {
                        "download_speed": traffic[0],
                        "download_unit": traffic[1],
                        "upload_speed": traffic[2],
                        "upload_unit": traffic[3],
                    },
                },
                "system": {
                    "uptime": {
                        "days": SystemOperations.get_uptime()[0],
                        "hours": SystemOperations.get_uptime()[1],
                        "minutes": SystemOperations.get_uptime()[2],
                    },
                    "updates_available": SystemOperations.check_updates(self.is_root),
                },
            }

            return metrics
        except Exception as e:
            logging.error(f"Failed to collect metrics: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


def create_app(is_root: bool = False) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ZlsNasDisplay Dashboard",
        description="Real-time monitoring dashboard for ZlsNasDisplay metrics",
        version="1.0.0",
    )

    metrics_collector = MetricsCollector(is_root=is_root)

    # Store active WebSocket connections
    active_connections: list[WebSocket] = []

    @app.get("/", response_class=HTMLResponse)
    async def get_dashboard() -> str:
        """Serve the main dashboard HTML page."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZlsNasDisplay Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .status {
            text-align: center;
            color: white;
            margin-bottom: 20px;
            font-size: 0.9em;
        }

        .status.connected {
            color: #4ade80;
        }

        .status.disconnected {
            color: #f87171;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.25);
        }

        .card-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 16px;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-weight: 500;
            color: #666;
        }

        .metric-value {
            font-size: 1.3em;
            font-weight: 700;
            color: #333;
        }

        .metric-value.good {
            color: #10b981;
        }

        .metric-value.warning {
            color: #f59e0b;
        }

        .metric-value.critical {
            color: #ef4444;
        }

        .icon {
            margin-right: 8px;
        }

        .timestamp {
            text-align: center;
            color: white;
            font-size: 0.85em;
            margin-top: 20px;
            opacity: 0.9;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ ZlsNasDisplay Dashboard</h1>
        <div class="status" id="connection-status">Connecting...</div>

        <div class="grid">
            <!-- CPU Card -->
            <div class="card">
                <div class="card-title">⚡ CPU</div>
                <div class="metric">
                    <span class="metric-label">Load</span>
                    <span class="metric-value" id="cpu-load">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Temperature</span>
                    <span class="metric-value" id="cpu-temp">--</span>
                </div>
            </div>

            <!-- Memory Card -->
            <div class="card">
                <div class="card-title">💾 Memory</div>
                <div class="metric">
                    <span class="metric-label">Usage</span>
                    <span class="metric-value" id="memory-usage">--</span>
                </div>
            </div>

            <!-- NVMe Card -->
            <div class="card">
                <div class="card-title">💿 NVMe Disk</div>
                <div class="metric">
                    <span class="metric-label">Usage</span>
                    <span class="metric-value" id="nvme-usage">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Temperature</span>
                    <span class="metric-value" id="nvme-temp">--</span>
                </div>
            </div>

            <!-- Fan Card -->
            <div class="card">
                <div class="card-title">🌀 Fan</div>
                <div class="metric">
                    <span class="metric-label">Speed</span>
                    <span class="metric-value" id="fan-speed">--</span>
                </div>
            </div>

            <!-- Network Card -->
            <div class="card">
                <div class="card-title">🌐 Network</div>
                <div class="metric">
                    <span class="metric-label">IP Address</span>
                    <span class="metric-value" id="ip-address" style="font-size: 1em;">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Signal</span>
                    <span class="metric-value" id="signal-strength">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Internet</span>
                    <span class="metric-value" id="internet-status">--</span>
                </div>
            </div>

            <!-- Traffic Card -->
            <div class="card">
                <div class="card-title">📊 Traffic</div>
                <div class="metric">
                    <span class="metric-label">⬇️ Download</span>
                    <span class="metric-value" id="download-speed">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">⬆️ Upload</span>
                    <span class="metric-value" id="upload-speed">--</span>
                </div>
            </div>

            <!-- System Card -->
            <div class="card">
                <div class="card-title">🖥️ System</div>
                <div class="metric">
                    <span class="metric-label">Uptime</span>
                    <span class="metric-value" id="uptime" style="font-size: 1em;">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Updates</span>
                    <span class="metric-value" id="updates">--</span>
                </div>
            </div>
        </div>

        <div class="timestamp" id="last-update">Last update: --</div>
    </div>

    <script>
        let ws = null;
        let reconnectInterval = null;

        function updateMetrics(data) {
            // Update timestamp
            const timestamp = new Date(data.timestamp);
            document.getElementById('last-update').textContent =
                `Last update: ${timestamp.toLocaleTimeString()}`;

            // CPU
            const cpuLoad = data.cpu.load;
            document.getElementById('cpu-load').textContent = `${cpuLoad}%`;
            document.getElementById('cpu-load').className = 'metric-value ' +
                (cpuLoad > 80 ? 'critical' : cpuLoad > 60 ? 'warning' : 'good');

            const cpuTemp = data.cpu.temperature;
            document.getElementById('cpu-temp').textContent = `${cpuTemp}°C`;
            document.getElementById('cpu-temp').className = 'metric-value ' +
                (cpuTemp > 70 ? 'critical' : cpuTemp > 60 ? 'warning' : 'good');

            // Memory
            const memUsage = data.memory.usage_percent;
            document.getElementById('memory-usage').textContent = `${memUsage}%`;
            document.getElementById('memory-usage').className = 'metric-value ' +
                (memUsage > 85 ? 'critical' : memUsage > 70 ? 'warning' : 'good');

            // NVMe
            const nvmeUsage = data.nvme.usage_percent;
            document.getElementById('nvme-usage').textContent = `${nvmeUsage}%`;
            document.getElementById('nvme-usage').className = 'metric-value ' +
                (nvmeUsage > 90 ? 'critical' : nvmeUsage > 75 ? 'warning' : 'good');

            const nvmeTemp = data.nvme.temperature;
            document.getElementById('nvme-temp').textContent = `${nvmeTemp}°C`;
            document.getElementById('nvme-temp').className = 'metric-value ' +
                (nvmeTemp > 60 ? 'critical' : nvmeTemp > 50 ? 'warning' : 'good');

            // Fan
            document.getElementById('fan-speed').textContent =
                `${data.fan.speed_rpm} RPM`;

            // Network
            document.getElementById('ip-address').textContent =
                data.network.ip_address || 'N/A';

            const signal = data.network.signal_strength_dbm;
            if (signal !== null) {
                document.getElementById('signal-strength').textContent = `${signal} dBm`;
                document.getElementById('signal-strength').className = 'metric-value ' +
                    (signal > -60 ? 'good' : signal > -70 ? 'warning' : 'critical');
            } else {
                document.getElementById('signal-strength').textContent = 'N/A';
            }

            document.getElementById('internet-status').textContent =
                data.network.internet_connected ? '✓ Connected' : '✗ Offline';
            document.getElementById('internet-status').className = 'metric-value ' +
                (data.network.internet_connected ? 'good' : 'critical');

            // Traffic
            document.getElementById('download-speed').textContent =
                `${data.network.traffic.download_speed.toFixed(2)} ${data.network.traffic.download_unit}/s`;
            document.getElementById('upload-speed').textContent =
                `${data.network.traffic.upload_speed.toFixed(2)} ${data.network.traffic.upload_unit}/s`;

            // System
            const uptime = data.system.uptime;
            document.getElementById('uptime').textContent =
                `${uptime.days}d ${uptime.hours}h ${uptime.minutes}m`;

            const updates = data.system.updates_available;
            document.getElementById('updates').textContent =
                updates === 0 ? '✓ Up to date' : `${updates} available`;
            document.getElementById('updates').className = 'metric-value ' +
                (updates === 0 ? 'good' : 'warning');
        }

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

            ws.onopen = () => {
                console.log('WebSocket connected');
                document.getElementById('connection-status').textContent = '🟢 Connected';
                document.getElementById('connection-status').className = 'status connected';

                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.error) {
                    console.error('Metrics error:', data.error);
                } else {
                    updateMetrics(data);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                document.getElementById('connection-status').textContent = '🔴 Disconnected - Reconnecting...';
                document.getElementById('connection-status').className = 'status disconnected';

                // Attempt to reconnect every 3 seconds
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(() => {
                        console.log('Attempting to reconnect...');
                        connectWebSocket();
                    }, 3000);
                }
            };
        }

        // Initial connection
        connectWebSocket();
    </script>
</body>
</html>
"""
        return html_content

    @app.get("/api/metrics")
    async def get_metrics() -> dict[str, Any]:
        """Get current system metrics as JSON."""
        return metrics_collector.get_all_metrics()

    @app.get("/api/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time metrics updates."""
        await websocket.accept()
        active_connections.append(websocket)

        try:
            while True:
                # Send metrics every 2 seconds
                metrics = metrics_collector.get_all_metrics()
                await websocket.send_json(metrics)
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            active_connections.remove(websocket)
            logging.info("WebSocket client disconnected")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
            if websocket in active_connections:
                active_connections.remove(websocket)

    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, is_root: bool = False) -> None:
    """Run the web dashboard server."""
    import uvicorn

    app = create_app(is_root=is_root)
    logging.info(f"Starting web dashboard on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Detect sudo
    IS_ROOT = os.getuid() == 0
    run_server(is_root=IS_ROOT)
