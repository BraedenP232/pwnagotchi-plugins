import logging
import os, time, sys
import html
import json

import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import *
from pwnagotchi.ui.view import BLACK
from PIL import ImageFont
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.utils as utils

try:
    sys.path.append(os.path.dirname(__file__))    
    from Touch_UI import Touch_Button as Button
except Exception as e:
    pass

from textwrap import TextWrapper
from flask import abort, jsonify
from flask import render_template_string

class Tweak_View2(plugins.Plugin):
    __author__ = 'Sniffleupagus,BraedenP232'
    __version__ = '1.2.0'
    __license__ = 'GPL3'
    __description__ = 'Modern UI layout editor with real-time preview and better UX'

    def __init__(self):
        self._agent = None
        self._start = time.time()
        self._logger = logging.getLogger(__name__)
        self._tweaks = {}
        self._untweak = {}
        self._already_updated = []
        self._history = []
        self._history_index = -1

        self.myFonts = {
            "Small": fonts.Small,
            "BoldSmall": fonts.BoldSmall,
            "Medium": fonts.Medium,
            "Bold": fonts.Bold,
            "BoldBig": fonts.BoldBig,
            "Huge": fonts.Huge
        }

    def get_ui_state(self):
        """Get current UI state as JSON for AJAX requests"""
        if not self._agent:
            return {"error": "Agent not available"}
        
        view = self._agent.view()
        state = {}
        
        for element_name, element in view._state._state.items():
            if isinstance(element, Widget):
                elem_data = {
                    "type": type(element).__name__,
                    "properties": {}
                }
                
                for key in dir(element):
                    if key.startswith("__") or key in ["draw", "value"]:
                        continue
                    
                    try:
                        val = getattr(element, key)
                        if key == "xy":
                            elem_data["properties"][key] = ",".join(map(str, val))
                        elif key in ["font", "text_font", "alt_font", "label_font"]:
                            font_name = "Unknown"
                            for name, font in self.myFonts.items():
                                if val == font:
                                    font_name = name
                                    break
                            elem_data["properties"][key] = font_name
                        elif type(val) in (int, str, float, bool):
                            elem_data["properties"][key] = val
                        elif type(val) in (list, tuple):
                            elem_data["properties"][key] = ",".join(map(str, val))
                    except:
                        pass
                
                state[element_name] = elem_data
        
        return state

    def get_modern_ui_template(self):
        """Return modern HTML/CSS/JS template with mobile support"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tweak View v2</title>
    <meta name="csrf_token" content="{{ csrf_token() }}">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .container {
            display: grid;
            grid-template-columns: 300px 1fr 350px;
            height: 100vh;
            gap: 0;
        }
        
        /* Mobile Layout */
        @media (max-width: 1024px) {
            .container {
                grid-template-columns: 1fr;
                height: auto;
                min-height: 100vh;
            }
            
            .sidebar, .properties-panel {
                display: none;
            }
            
            .sidebar.active, .properties-panel.active {
                display: block;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 1000;
                overflow-y: auto;
            }
            
            .properties-panel.active {
                top: 60px;
            }
        }
        
        .sidebar {
            background: #1a1a1a;
            border-right: 1px solid #333;
            overflow-y: auto;
            padding: 20px;
        }
        
        .main-content {
            background: #151515;
            overflow-y: auto;
            padding: 20px;
            padding-top: 70px;
        }
        
        @media (max-width: 1024px) {
            .main-content {
                padding: 10px;
                padding-top: 60px;
            }
        }
        
        .properties-panel {
            background: #1a1a1a;
            border-left: 1px solid #333;
            overflow-y: auto;
            padding: 20px;
        }
        
        /* Mobile Navigation Bar */
        .mobile-nav {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: #1a1a1a;
            border-bottom: 1px solid #333;
            z-index: 999;
            padding: 0 15px;
            align-items: center;
            justify-content: space-between;
        }
        
        @media (max-width: 1024px) {
            .mobile-nav {
                display: flex;
            }
        }
        
        .mobile-nav-title {
            font-size: 16px;
            font-weight: 600;
            color: #00ff88;
        }
        
        .mobile-nav-buttons {
            display: flex;
            gap: 10px;
        }
        
        .nav-btn {
            padding: 8px 12px;
            background: #252525;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .nav-btn:active {
            background: #00ff88;
            color: #0f0f0f;
        }
        
        .nav-btn.active {
            background: #00ff88;
            color: #0f0f0f;
            border-color: #00ff88;
        }
        
        .close-panel {
            position: absolute;
            top: 15px;
            right: 15px;
            background: #ff4444;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            z-index: 10;
        }
        
        h1, h2, h3 {
            color: #00ff88;
            margin-bottom: 15px;
        }
        
        h1 { font-size: 24px; }
        h2 { font-size: 18px; margin-top: 20px; }
        h3 { font-size: 16px; }
        
        @media (max-width: 768px) {
            h1 { font-size: 20px; }
            h2 { font-size: 16px; }
            h3 { font-size: 14px; }
        }
        
        .search-box {
            width: 100%;
            padding: 10px;
            background: #252525;
            border: 1px solid #444;
            border-radius: 6px;
            color: #e0e0e0;
            margin-bottom: 15px;
            font-size: 14px;
        }
        
        .element-list {
            list-style: none;
        }
        
        .element-item {
            padding: 10px;
            margin-bottom: 5px;
            background: #252525;
            border: 1px solid #333;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .element-item:hover {
            background: #2a2a2a;
            border-color: #00ff88;
        }
        
        .element-item.active {
            background: #1a3a2a;
            border-color: #00ff88;
        }
        
        .element-type {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
        }
        
        .preview-container {
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 300px;
            overflow-x: auto;
        }
        
        @media (max-width: 768px) {
            .preview-container {
                padding: 10px;
                min-height: 200px;
                border-radius: 4px;
            }
        }
        
        .preview-img {
            width: 100%;
            max-width: 800px;
            height: auto;
            border: 2px solid #333;
            border-radius: 4px;
            image-rendering: crisp-edges;
            image-rendering: pixelated;
        }
        
        @media (max-width: 768px) {
            .preview-img {
                max-width: 100%;
            }
        }
        
        .property-group {
            margin-bottom: 20px;
            padding: 15px;
            background: #252525;
            border-radius: 6px;
        }
        
        .property-row {
            margin-bottom: 12px;
        }
        
        .xy-controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 5px;
        }
        
        @media (max-width: 480px) {
            .xy-controls {
                grid-template-columns: 1fr;
            }
        }
        
        .xy-input-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .xy-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 4px;
            margin-top: 4px;
        }
        
        .xy-btn {
            padding: 8px 4px;
            background: #333;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.2s;
            white-space: nowrap;
        }
        
        @media (max-width: 480px) {
            .xy-btn {
                font-size: 10px;
                padding: 6px 2px;
            }
        }
        
        .xy-btn:hover {
            background: #444;
            border-color: #00ff88;
        }
        
        .xy-btn:active {
            background: #00ff88;
            color: #0f0f0f;
        }
        
        label {
            display: block;
            color: #aaa;
            font-size: 13px;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        input[type="text"], input[type="number"], select {
            width: 100%;
            padding: 10px;
            background: #1a1a1a;
            border: 1px solid #444;
            border-radius: 4px;
            color: #e0e0e0;
            font-size: 14px;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #00ff88;
        }
        
        .btn {
            padding: 10px 20px;
            background: #00ff88;
            color: #0f0f0f;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
            margin-right: 10px;
            margin-bottom: 10px;
            white-space: nowrap;
        }
        
        @media (max-width: 768px) {
            .btn {
                padding: 8px 16px;
                font-size: 13px;
                margin-right: 5px;
            }
        }
        
        .btn:hover {
            background: #00dd77;
            transform: translateY(-1px);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn-secondary {
            background: #444;
            color: #e0e0e0;
        }
        
        .btn-secondary:hover {
            background: #555;
        }
        
        .btn-danger {
            background: #ff4444;
            color: white;
        }
        
        .btn-danger:hover {
            background: #dd2222;
        }
        
        .actions {
            display: flex;
            gap: 5px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            left: 20px;
            max-width: 400px;
            margin: 0 auto;
            padding: 15px 20px;
            background: #00ff88;
            color: #0f0f0f;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 2000;
            animation: slideIn 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .notification {
                top: 70px;
                left: 10px;
                right: 10px;
                font-size: 14px;
            }
        }
        
        .notification.error {
            background: #ff4444;
            color: white;
        }
        
        .refresh-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 12px;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 6px;
            color: #00ff88;
            font-size: 12px;
            display: none;
            align-items: center;
            gap: 8px;
            z-index: 1001;
        }
        
        @media (max-width: 768px) {
            .refresh-indicator {
                top: 70px;
                right: 10px;
                left: auto;
            }
        }
        
        .refresh-indicator.active {
            display: flex;
        }
        
        .spinner {
            width: 12px;
            height: 12px;
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-top-color: #00ff88;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes slideIn {
            from { transform: translateY(-20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: #252525;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        
        @media (max-width: 480px) {
            .stat-card {
                padding: 10px;
            }
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
        }
        
        @media (max-width: 480px) {
            .stat-value {
                font-size: 20px;
            }
        }
        
        .stat-label {
            font-size: 12px;
            color: #888;
        }
        
        .modified-badge {
            display: inline-block;
            background: #ff8800;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 5px;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1a1a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #444;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        
        /* Overlay for mobile panels */
        .overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 998;
        }
        
        .overlay.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="overlay" id="overlay" onclick="closeAllPanels()"></div>
    
    <div class="mobile-nav">
        <div class="mobile-nav-title">Tweak View v2 by Sniffleupagus, modified by BraedenP232</div>
        <div class="mobile-nav-buttons">
            <button class="nav-btn" onclick="toggleSidebar()">📋 Elements</button>
            <button class="nav-btn" onclick="toggleProperties()" id="propertiesBtn">⚙️ Properties</button>
        </div>
    </div>
    
    <div class="refresh-indicator" id="refreshIndicator">
        <div class="spinner"></div>
        <span>Refreshing...</span>
    </div>
    
    <div class="container">
        <div class="sidebar" id="sidebar">
            <button class="close-panel" onclick="closeAllPanels()">✕ Close</button>
            <h2>UI Elements</h2>
            <input type="text" class="search-box" id="searchBox" placeholder="Search elements...">
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalElements">0</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="modifiedElements">0</div>
                    <div class="stat-label">Modified</div>
                </div>
            </div>
            
            <ul class="element-list" id="elementList">
                <li class="loading">Loading elements...</li>
            </ul>
        </div>
        
        <div class="main-content">
            <h1>Tweak View v2</h1>
            
            <div class="preview-container">
                <img id="preview" class="preview-img" src="/ui?{{ timestamp }}" alt="UI Preview">
            </div>
            
            <div class="actions">
                <button class="btn" onclick="refreshPreview()">🔄 Refresh</button>
                <button class="btn btn-secondary" onclick="exportConfig()">💾 Export</button>
                <button class="btn btn-secondary" onclick="importConfig()">📂 Import</button>
                <button class="btn btn-danger" onclick="resetAll()">🔄 Reset</button>
            </div>
        </div>
        
        <div class="properties-panel" id="propertiesPanel">
            <button class="close-panel" onclick="closeAllPanels()">✕ Close</button>
            <h2>Properties</h2>
            <div id="propertiesContent">
                <p style="color: #888; padding: 20px; text-align: center;">
                    Select an element to edit its properties
                </p>
            </div>
        </div>
    </div>

    <script>
        const csrfToken = document.querySelector('meta[name="csrf_token"]').content;
        let currentElement = null;
        let uiState = {};
        let modifiedElements = new Set();
        
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            const propertiesPanel = document.getElementById('propertiesPanel');
            
            propertiesPanel.classList.remove('active');
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        }
        
        function toggleProperties() {
            const propertiesPanel = document.getElementById('propertiesPanel');
            const overlay = document.getElementById('overlay');
            const sidebar = document.getElementById('sidebar');
            
            sidebar.classList.remove('active');
            propertiesPanel.classList.toggle('active');
            overlay.classList.toggle('active');
        }
        
        function closeAllPanels() {
            document.getElementById('sidebar').classList.remove('active');
            document.getElementById('propertiesPanel').classList.remove('active');
            document.getElementById('overlay').classList.remove('active');
        }
        
        async function fetchUIState() {
            try {
                const response = await fetch('/plugins/tweak_view2/api/state');
                uiState = await response.json();
                renderElementList();
                updateStats();
            } catch (error) {
                showNotification('Failed to load UI state', 'error');
            }
        }
        
        function renderElementList() {
            const list = document.getElementById('elementList');
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            
            list.innerHTML = '';
            
            Object.entries(uiState).forEach(([name, data]) => {
                if (searchTerm && !name.toLowerCase().includes(searchTerm)) {
                    return;
                }
                
                const li = document.createElement('li');
                li.className = 'element-item';
                if (currentElement === name) li.classList.add('active');
                
                const isModified = modifiedElements.has(name);
                li.innerHTML = `
                    <div>${name}${isModified ? '<span class="modified-badge">MOD</span>' : ''}</div>
                    <div class="element-type">${data.type}</div>
                `;
                
                li.onclick = () => selectElement(name);
                list.appendChild(li);
            });
        }
        
        function selectElement(name) {
            currentElement = name;
            renderElementList();
            renderProperties();
            
            // On mobile, automatically show properties panel
            if (window.innerWidth <= 1024) {
                closeAllPanels();
                setTimeout(() => toggleProperties(), 100);
            }
        }
        
        function renderProperties() {
            const panel = document.getElementById('propertiesContent');
            if (!currentElement || !uiState[currentElement]) {
                panel.innerHTML = '<p style="color: #888;">Select an element</p>';
                return;
            }
            
            const data = uiState[currentElement].properties;
            let html = `<h3>${currentElement}</h3>`;
            
            const filteredProps = Object.entries(data).filter(([key]) => 
                key !== 'color' && !key.startsWith('_')
            );
            
            filteredProps.forEach(([key, value]) => {
                html += `<div class="property-row">`;
                html += `<label>${key}</label>`;
                
                if (key === 'xy') {
                    const [x, y] = value.split(',').map(v => v.trim());
                    html += `<div class="xy-controls">
                        <div class="xy-input-group">
                            <label style="font-size: 11px; color: #666;">X Position</label>
                            <input type="number" id="prop_xy_x" value="${x}" 
                                   onchange="updateXY('${key}', this.value, document.getElementById('prop_xy_y').value)">
                            <div class="xy-buttons">
                                <button class="xy-btn" onclick="adjustXY('x', -10)">◄◄</button>
                                <button class="xy-btn" onclick="adjustXY('x', -1)">◄</button>
                                <button class="xy-btn" onclick="adjustXY('x', 1)">►</button>
                                <button class="xy-btn" onclick="adjustXY('x', 10)">►►</button>
                            </div>
                        </div>
                        <div class="xy-input-group">
                            <label style="font-size: 11px; color: #666;">Y Position</label>
                            <input type="number" id="prop_xy_y" value="${y}" 
                                   onchange="updateXY('${key}', document.getElementById('prop_xy_x').value, this.value)">
                            <div class="xy-buttons">
                                <button class="xy-btn" onclick="adjustXY('y', -10)">▲▲</button>
                                <button class="xy-btn" onclick="adjustXY('y', -1)">▲</button>
                                <button class="xy-btn" onclick="adjustXY('y', 1)">▼</button>
                                <button class="xy-btn" onclick="adjustXY('y', 10)">▼▼</button>
                            </div>
                        </div>
                    </div>`;
                } else if (key.includes('font')) {
                    html += `<select id="prop_${key}" onchange="updateProperty('${key}', this.value)">`;
                    html += `<option selected>${value}</option>`;
                    html += `</select>`;
                } else {
                    html += `<input type="text" id="prop_${key}" value="${value}" 
                             onchange="updateProperty('${key}', this.value)">`;
                }
                
                html += `</div>`;
            });
            
            html += `<div class="actions">
                <button class="btn" onclick="applyChanges()">Apply</button>
                <button class="btn btn-secondary" onclick="revertElement()">Revert</button>
            </div>`;
            
            panel.innerHTML = html;
        }
        
        function updateXY(key, x, y) {
            if (!currentElement) return;
            const xyValue = `${x},${y}`;
            uiState[currentElement].properties[key] = xyValue;
            modifiedElements.add(currentElement);
            updateStats();
            renderElementList();
        }
        
        function adjustXY(axis, amount) {
            const xInput = document.getElementById('prop_xy_x');
            const yInput = document.getElementById('prop_xy_y');
            
            if (axis === 'x') {
                xInput.value = parseInt(xInput.value) + amount;
            } else {
                yInput.value = parseInt(yInput.value) + amount;
            }
            
            updateXY('xy', xInput.value, yInput.value);
            applyChanges();
        }
        
        async function updateProperty(key, value) {
            if (!currentElement) return;
            
            uiState[currentElement].properties[key] = value;
            modifiedElements.add(currentElement);
            updateStats();
            renderElementList();
        }
        
        async function applyChanges() {
            if (!currentElement) return;
            
            try {
                const response = await fetch('/plugins/tweak_view2/api/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        element: currentElement,
                        properties: uiState[currentElement].properties
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showNotification('Changes applied successfully');
                    setTimeout(() => refreshPreview(), 500);
                } else {
                    showNotification(result.error || 'Failed to apply changes', 'error');
                }
            } catch (error) {
                console.error('Apply error:', error);
                showNotification('Error applying changes', 'error');
            }
        }
        
        function refreshPreview() {
            const img = document.getElementById('preview');
            const indicator = document.getElementById('refreshIndicator');
            const timestamp = Date.now();
            
            indicator.classList.add('active');
            
            img.onload = () => {
                setTimeout(() => indicator.classList.remove('active'), 300);
            };
            
            img.onerror = () => {
                indicator.classList.remove('active');
            };
            
            img.src = `/ui?t=${timestamp}`;
        }
        
        async function revertElement() {
            if (!currentElement) return;
            
            if (!confirm(`Revert all changes to ${currentElement}?`)) return;
            
            try {
                const response = await fetch('/plugins/tweak_view2/api/revert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        element: currentElement
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showNotification('Element reverted');
                    modifiedElements.delete(currentElement);
                    await fetchUIState();
                    setTimeout(() => refreshPreview(), 500);
                } else {
                    showNotification('Failed to revert', 'error');
                }
            } catch (error) {
                showNotification('Error reverting', 'error');
            }
        }
        
        function showNotification(message, type = 'success') {
            const notif = document.createElement('div');
            notif.className = `notification ${type}`;
            notif.textContent = message;
            document.body.appendChild(notif);
            
            setTimeout(() => notif.remove(), 3000);
        }
        
        function updateStats() {
            document.getElementById('totalElements').textContent = Object.keys(uiState).length;
            document.getElementById('modifiedElements').textContent = modifiedElements.size;
        }
        
        function exportConfig() {
            showNotification('Export feature coming soon');
        }
        
        function importConfig() {
            showNotification('Import feature coming soon');
        }
        
        function resetAll() {
            if (confirm('Reset all changes?')) {
                showNotification('Reset feature coming soon');
            }
        }
        
        document.getElementById('searchBox').addEventListener('input', renderElementList);
        
        setInterval(refreshPreview, 5000);
        
        fetchUIState();
    </script>
</body>
</html>
"""

    def on_webhook(self, path, request):
        try:
            if not self._agent and self._ui:
                self._agent = self._ui._agent

            if path is None:
                path = ""
            
            if path.startswith("api/"):
                if path == "api/state":
                    return jsonify(self.get_ui_state())
                
                elif path == "api/update" and request.method == "POST":
                    data = request.get_json()
                    element = data.get('element')
                    properties = data.get('properties')
                    
                    self._logger.info(f"Updating element: {element}")
                    self._logger.info(f"Properties: {properties}")
                    
                    for key, value in properties.items():
                        if key == 'color':
                            continue
                        tag = f"VSS.{element}.{key}"
                        self._tweaks[tag] = value
                        self._logger.info(f"Set tweak: {tag} = {value}")
                    
                    try:
                        with open(self._conf_file, "w") as f:
                            f.write(json.dumps(self._tweaks, indent=4))
                        self._logger.info("Saved tweaks to file")
                        
                        self._already_updated = []
                        self._logger.info("Cleared all update flags")
                        
                        self.update_elements(self._ui)
                        self._logger.info("Applied updates to UI")
                        
                        if hasattr(self._ui, 'update'):
                            self._ui.update(force=True)
                        
                        return jsonify({"success": True})
                    except Exception as err:
                        self._logger.error(f"Update error: {err}")
                        return jsonify({"success": False, "error": str(err)}), 500
                
                elif path == "api/revert" and request.method == "POST":
                    data = request.get_json()
                    element = data.get('element')
                    
                    keys_to_remove = [k for k in self._tweaks.keys() if k.startswith(f"VSS.{element}.")]
                    for key in keys_to_remove:
                        if key in self._untweak:
                            vss, elem, prop = key.split(".")
                            if hasattr(self._ui._state._state[elem], prop):
                                setattr(self._ui._state._state[elem], prop, self._untweak[key])
                        del self._tweaks[key]
                    
                    with open(self._conf_file, "w") as f:
                        f.write(json.dumps(self._tweaks, indent=4))
                    
                    return jsonify({"success": True})

            if request.method == "GET" and (path == "/" or not path):
                timestamp = int(time.time())
                return render_template_string(self.get_modern_ui_template(), timestamp=timestamp)
            
            abort(404)
            
        except Exception as err:
            self._logger.warning("webhook err: %s" % repr(err))
            return jsonify({"error": str(err)}), 500

    def on_loaded(self):
        self._start = time.time()
        self._state = 0
        self._next = 0

    def on_ready(self, agent):
        logging.info("Tweakview v2.0 ready")
        self._agent = agent

    def on_unload(self, ui):
        try:
            state = ui._state._state
            for tag, value in self._untweak.items():
                vss, element, key = tag.split(".")
                if key in dir(ui._state._state[element]):
                    if hasattr(ui._state._state[element], key):
                        setattr(ui._state._state[element], key, value)
        except Exception as err:
            self._logger.warning("ui unload: %s" % repr(err))

    def on_ui_setup(self, ui):
        self._ui = ui

        self.myFonts = {
            "Small": fonts.Small,
            "BoldSmall": fonts.BoldSmall,
            "Medium": fonts.Medium,
            "Bold": fonts.Bold,
            "BoldBig": fonts.BoldBig,
            "Huge": fonts.Huge
        }
        
        just_once = True
        for p in [6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 25, 28, 30, 35, 42, 48, 52, 54, 60, 69, 72, 80, 90, 100, 120]:
            try:
                self.myFonts["Deja %s" % p] = ImageFont.truetype('DejaVuSansMono', p)
                self.myFonts["DejaB %s" % p] = ImageFont.truetype('DejaVuSansMono-Bold', p)
                self.myFonts["DejaO %s" % p] = ImageFont.truetype('DejaVuSansMono-Oblique', p)
            except Exception as e:
                if just_once:
                    logging.warn("Missing some fonts: %s" % repr(e))
                    just_once = False

        self._conf_file = self.options.get("filename", "/etc/pwnagotchi/tweak_view2.json")

        try:
            if os.path.isfile(self._conf_file):
                with open(self._conf_file, 'r') as f:
                    self._tweaks = json.load(f)

            self._already_updated = []
            self._logger.info("Tweak view v2.0 ready.")

        except Exception as err:
            self._logger.warn("TweakUI loading failed: %s" % repr(err))

        try:
            self.update_elements(ui)
        except Exception as err:
            self._logger.warning("ui setup: %s" % repr(err))

    def on_ui_update(self, ui):
        self.update_elements(ui)
        
    def update_elements(self, ui):
        try:
            state = ui._state._state
            
            for tag, value in self._tweaks.items():
                vss, element, key = tag.split(".")
                
                try:
                    if element in state and key in dir(state[element]):
                        if tag not in self._untweak:
                            self._untweak[tag] = getattr(ui._state._state[element], key)
                            self._logger.debug(f"Backed up {tag} = {self._untweak[tag]}")

                        if key == "xy":
                            new_xy = value.split(",")
                            new_xy = [int(float(x.strip())) for x in new_xy]
                            if new_xy[0] < 0: new_xy[0] = ui.width() + new_xy[0]
                            if new_xy[1] < 0: new_xy[1] = ui.height() + new_xy[1]
                            ui._state._state[element].xy = new_xy
                            self._logger.debug(f"Updated {element}.xy to {new_xy}")
                        elif key in ["font", "text_font", "alt_font", "label_font"]:
                            if value in self.myFonts:
                                setattr(ui._state._state[element], key, self.myFonts[value])
                                self._logger.debug(f"Updated {element}.{key} to {value}")
                        elif key in ["bgcolor", "color", "label"]:
                            setattr(ui._state._state[element], key, value)
                            self._logger.debug(f"Updated {element}.{key} to {value}")
                        elif key == "label_spacing":
                            ui._state._state[element].label_spacing = int(value)
                            self._logger.debug(f"Updated {element}.label_spacing to {value}")
                        elif key == "max_length":
                            uie = ui._state._state[element]
                            uie.max_length = int(value)
                            uie.wrapper = TextWrapper(width=int(value), replace_whitespace=False) if uie.wrap else None
                            self._logger.debug(f"Updated {element}.max_length to {value}")
                    elif element not in state:
                        self._logger.debug(f"Element {element} not in state")
                except Exception as err:
                    self._logger.warn("tweak failed for key %s: %s" % (tag, repr(err)))
                    
        except Exception as err:
            self._logger.warning("ui update: %s" % repr(err))