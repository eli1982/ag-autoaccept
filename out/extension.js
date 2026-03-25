"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const fs = require("fs");
function activate(context) {
    let pythonProcess;
    let statusBarItem;
    let clickCounter = context.globalState.get('clicksSaved', 0);
    let autoStart = context.globalState.get('autoStart', false);
    let outputChannel = vscode.window.createOutputChannel('Antigravity Auto-Accept');
    let logBuffer = [];
    let viewProvider;
    // --- Status Bar Setup ---
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'ag-autoaccept.toggle';
    context.subscriptions.push(statusBarItem);
    function updateUI(active = !!pythonProcess) {
        statusBarItem.text = `$(zap)`;
        statusBarItem.color = active ? '#0078D4' : undefined;
        statusBarItem.tooltip = `Antigravity Auto-Accept. Total Clicks Saved: ${clickCounter}`;
        statusBarItem.show();
        if (viewProvider) {
            viewProvider.updateState(active, clickCounter, logBuffer.slice(-10));
        }
    }
    // --- Process Management ---
    function startEngine() {
        if (pythonProcess)
            return;
        const scriptPath = path.join(context.extensionPath, 'auto_accept.py');
        const pythonPath = vscode.workspace.getConfiguration('ag-autoaccept').get('pythonPath', 'python');
        context.globalState.update('autoStart', true);
        outputChannel.appendLine(`[Extension] Starting Python engine: ${pythonPath} ${scriptPath}`);
        pythonProcess = cp.spawn(pythonPath, [scriptPath, '--ipc'], {
            cwd: context.extensionPath,
            shell: true
        });
        pythonProcess.stdout?.on('data', (data) => {
            const lines = data.toString().split('\n');
            for (const line of lines) {
                if (!line.trim())
                    continue;
                try {
                    const msg = JSON.parse(line);
                    handleIPC(msg);
                }
                catch (e) {
                    outputChannel.appendLine(`[Python] ${line}`);
                    appendToRollingLog(line);
                }
            }
        });
        let stderrData = '';
        pythonProcess.stderr?.on('data', (data) => {
            const msg = data.toString();
            stderrData += msg;
            outputChannel.appendLine(`[stderr] ${msg}`);
        });
        pythonProcess.on('error', (err) => {
            outputChannel.appendLine(`[Extension] Failed to start Python process: ${err.message}`);
            vscode.window.showErrorMessage(`Failed to start Python engine: ${err.message}. Check your pythonPath setting.`);
            pythonProcess = undefined;
            updateUI(false);
        });
        pythonProcess.on('close', (code, signal) => {
            outputChannel.appendLine(`[Extension] Python engine exited. Code: ${code}, Signal: ${signal}`);
            if (code !== 0 && code !== null) {
                vscode.window.showErrorMessage(`Python engine exited with code ${code}. ${stderrData ? 'Error: ' + stderrData.slice(-200) : 'Check Output channel for details.'}`);
            }
            pythonProcess = undefined;
            updateUI(false);
        });
        updateUI(true);
    }
    function stopEngine() {
        if (pythonProcess) {
            pythonProcess.kill();
            pythonProcess = undefined;
        }
        context.globalState.update('autoStart', false);
        updateUI(false);
    }
    function handleIPC(msg) {
        if (msg.type === 'click') {
            clickCounter += (msg.saved || 1);
            context.globalState.update('clicksSaved', clickCounter);
            updateUI();
        }
        else if (msg.type === 'log') {
            outputChannel.appendLine(`[Python] ${msg.message}`);
            appendToRollingLog(msg.message);
        }
    }
    // --- Log Management ---
    function appendToRollingLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        const logLine = `[${timestamp}] ${message}`;
        logBuffer.push(logLine);
        if (logBuffer.join('\n').length > 1024) {
            logBuffer.shift();
        }
        const logPath = path.join(context.globalStorageUri.fsPath, 'rolling.log');
        if (!fs.existsSync(context.globalStorageUri.fsPath)) {
            fs.mkdirSync(context.globalStorageUri.fsPath, { recursive: true });
        }
        fs.writeFileSync(logPath, logBuffer.join('\n'));
        updateUI();
    }
    // --- Sidebar View ---
    viewProvider = new AutoAcceptViewProvider(context.extensionUri);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('ag-autoaccept-view', viewProvider));
    viewProvider.onToggle(() => {
        if (pythonProcess)
            stopEngine();
        else
            startEngine();
    });
    // --- Commands ---
    context.subscriptions.push(vscode.commands.registerCommand('ag-autoaccept.toggle', () => {
        if (pythonProcess)
            stopEngine();
        else
            startEngine();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('ag-autoaccept.showLogs', () => {
        outputChannel.show();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('ag-autoaccept.openDashboard', () => {
        vscode.commands.executeCommand('workbench.view.extension.ag-autoaccept-panel');
    }));
    context.subscriptions.push(vscode.commands.registerCommand('ag-autoaccept.installDeps', () => {
        const pythonPath = vscode.workspace.getConfiguration('ag-autoaccept').get('pythonPath', 'python');
        const terminal = vscode.window.createTerminal('Auto-Accept Setup');
        terminal.show();
        terminal.sendText(`${pythonPath} -m pip install pyautogui pygetwindow opencv-python --user`);
        vscode.window.showInformationMessage('Installing Python dependencies in terminal...');
    }));
    // --- Activity Monitoring ---
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(() => {
        if (pythonProcess && pythonProcess.stdin) {
            pythonProcess.stdin.write('heartbeat\n');
        }
    }));
    if (autoStart) {
        startEngine();
    }
    else {
        updateUI(false);
    }
}
class AutoAcceptViewProvider {
    _extensionUri;
    _view;
    _onToggleEmitter = new vscode.EventEmitter();
    onToggle = this._onToggleEmitter.event;
    constructor(_extensionUri) {
        this._extensionUri = _extensionUri;
    }
    resolveWebviewView(webviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        webviewView.webview.onDidReceiveMessage(data => {
            if (data.type === 'toggle') {
                this._onToggleEmitter.fire();
            }
            else if (data.type === 'installDeps') {
                vscode.commands.executeCommand('ag-autoaccept.installDeps');
            }
        });
    }
    updateState(active, count, logs) {
        if (this._view) {
            this._view.webview.postMessage({ type: 'update', active, count, logs });
        }
    }
    _getHtmlForWebview(webview) {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <style>
                    :root {
                        --accent: #007acc;
                        --accent-hover: #0062a3;
                        --bg: var(--vscode-sideBar-background);
                        --card-bg: var(--vscode-editor-background);
                        --border: var(--vscode-widget-border);
                        --text: var(--vscode-foreground);
                        --text-muted: var(--vscode-descriptionForeground);
                    }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        padding: 20px; 
                        display: flex; 
                        flex-direction: column; 
                        gap: 20px;
                        background-color: var(--bg);
                        color: var(--text);
                        margin: 0;
                    }
                    .header {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        margin-bottom: 5px;
                    }
                    .header h2 { margin: 0; font-size: 1.2em; font-weight: 600; }
                    .card { 
                        background: var(--card-bg); 
                        border: 1px solid var(--border); 
                        padding: 20px; 
                        border-radius: 12px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        transition: transform 0.2s ease;
                    }
                    .card:hover { transform: translateY(-2px); }
                    .counter-box { text-align: center; }
                    .counter { 
                        font-size: 3em; 
                        font-weight: 800; 
                        background: linear-gradient(135deg, #007acc, #48b1bf);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin: 10px 0;
                        font-variant-numeric: tabular-nums;
                    }
                    .status-container {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .status-pill {
                        padding: 4px 12px;
                        border-radius: 20px;
                        font-size: 0.75em;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }
                    .status-pill.on { background: rgba(76, 175, 80, 0.15); color: #4caf50; border: 1px solid rgba(76, 175, 80, 0.3); }
                    .status-pill.off { background: rgba(244, 67, 54, 0.15); color: #f44336; border: 1px solid rgba(244, 67, 54, 0.3); }
                    
                    button { 
                        background: linear-gradient(135deg, var(--accent), #48b1bf);
                        color: white; 
                        border: none; 
                        padding: 12px; 
                        cursor: pointer; 
                        border-radius: 8px; 
                        width: 100%; 
                        font-weight: 600;
                        font-size: 1em;
                        transition: all 0.2s ease;
                        box-shadow: 0 4px 10px rgba(0,122,204,0.3);
                        margin-top: 15px;
                    }
                    button:hover { filter: brightness(1.1); transform: scale(1.02); }
                    button:active { transform: scale(0.98); }
                    button.stop { background: linear-gradient(135deg, #f44336, #e91e63); box-shadow: 0 4px 10px rgba(244,67,54,0.3); }

                    .section-title { font-size: 0.8em; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
                    .logs { 
                        font-family: 'Consolas', monospace;
                        font-size: 0.8em; 
                        background: rgba(0,0,0,0.3); 
                        padding: 12px; 
                        border-radius: 8px; 
                        height: 180px; 
                        overflow-y: auto; 
                        border: 1px solid var(--border);
                    }
                    .log-entry { 
                        border-bottom: 1px solid rgba(255,255,255,0.03); 
                        padding: 4px 0; 
                        color: #ccc;
                        word-break: break-all;
                    }
                    .log-time { color: var(--accent); margin-right: 8px; opacity: 0.8; }
                </style>
            </head>
            <body>
                <div class="header">
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor"><path d="M10 1L3 9H7L6 15L13 7H9L10 1Z"/></svg>
                    <h2>Dashboard</h2>
                </div>

                <div class="card">
                    <div class="status-container">
                        <span class="section-title">Engine Status</span>
                        <div id="status-pill" class="status-pill off">Inactive</div>
                    </div>
                    <button id="toggle-btn" onclick="toggle()">Start Engine</button>
                    <button id="install-btn" style="margin-top: 10px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);" onclick="installDeps()">Install Dependencies</button>
                </div>

                <div class="card counter-box">
                    <span class="section-title">Clicks Saved</span>
                    <div id="click-count" class="counter">0</div>
                    <div style="font-size: 0.8em; color: var(--text-muted);">Across all sessions</div>
                </div>

                <div>
                    <span class="section-title">Live Logs</span>
                    <div class="logs" id="log-container">
                        <div class="log-entry"><span class="log-time">System</span> Ready.</div>
                    </div>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();
                    function toggle() { vscode.postMessage({ type: 'toggle' }); }
                    function installDeps() { vscode.postMessage({ type: 'installDeps' }); }
                    window.addEventListener('message', event => {
                        const msg = event.data;
                        if (msg.type === 'update') {
                            const pill = document.getElementById('status-pill');
                            pill.innerText = msg.active ? 'Active' : 'Inactive';
                            pill.className = 'status-pill ' + (msg.active ? 'on' : 'off');
                            
                            const btn = document.getElementById('toggle-btn');
                            btn.innerText = msg.active ? 'Stop Engine' : 'Start Engine';
                            btn.className = msg.active ? 'stop' : '';
                            
                            document.getElementById('click-count').innerText = msg.count;
                            
                            const logContainer = document.getElementById('log-container');
                            if (msg.logs && msg.logs.length > 0) {
                                logContainer.innerHTML = msg.logs.map(l => {
                                    const parts = l.match(/\\[(.*?)\\] (.*)/);
                                    if (parts) {
                                        return '<div class="log-entry"><span class="log-time">' + parts[1] + '</span>' + parts[2] + '</div>';
                                    }
                                    return '<div class="log-entry">' + l + '</div>';
                                }).join('');
                                logContainer.scrollTop = logContainer.scrollHeight;
                            }
                        }
                    });
                </script>
            </body>
            </html>`;
    }
}
//# sourceMappingURL=extension.js.map