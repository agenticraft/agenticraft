// AgentiCraft Visual Builder JavaScript

class VisualBuilder {
    constructor() {
        this.workflowId = null;
        this.selectedComponent = null;
        this.components = new Map();
        this.connections = [];
        this.isConnecting = false;
        this.connectionStart = null;
        
        this.init();
    }
    
    async init() {
        // Create new workflow
        await this.createWorkflow();
        
        // Set up event listeners
        this.setupDragAndDrop();
        this.setupTemplates();
        this.setupButtons();
        this.setupCanvas();
        
        // Show toast
        this.showToast('Visual Builder ready! Drag components or load a template to start.');
    }
    
    async createWorkflow() {
        try {
            const response = await fetch('/api/workflows/create', {
                method: 'POST'
            });
            const data = await response.json();
            this.workflowId = data.workflow_id;
        } catch (error) {
            this.showToast('Failed to create workflow', 'error');
        }
    }
    
    setupDragAndDrop() {
        // Component palette drag start
        document.querySelectorAll('.component-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('componentType', item.dataset.type);
                item.classList.add('dragging');
            });
            
            item.addEventListener('dragend', (e) => {
                item.classList.remove('dragging');
            });
        });
        
        // Canvas drop
        const canvas = document.getElementById('canvas');
        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        canvas.addEventListener('drop', async (e) => {
            e.preventDefault();
            const componentType = e.dataTransfer.getData('componentType');
            
            if (componentType) {
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                await this.addComponent(componentType, x, y);
            }
        });
    }
    
    setupTemplates() {
        document.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', async () => {
                const templateId = card.dataset.template;
                await this.loadTemplate(templateId);
            });
        });
    }
    
    setupButtons() {
        // Export button
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportWorkflow();
        });
        
        // Save button
        document.getElementById('saveBtn').addEventListener('click', () => {
            this.saveWorkflow();
        });
        
        // Load button
        document.getElementById('loadBtn').addEventListener('click', () => {
            this.showLoadModal();
        });
        
        // Modal buttons
        document.getElementById('closeModalBtn').addEventListener('click', () => {
            this.hideModal('exportModal');
        });
        
        document.getElementById('closeLoadModalBtn').addEventListener('click', () => {
            this.hideModal('loadModal');
        });
        
        document.getElementById('copyCodeBtn').addEventListener('click', () => {
            this.copyCode();
        });
        
        document.getElementById('downloadCodeBtn').addEventListener('click', () => {
            this.downloadCode();
        });
    }
    
    setupCanvas() {
        const canvas = document.getElementById('canvas');
        
        // Click on canvas to deselect
        canvas.addEventListener('click', (e) => {
            if (e.target === canvas || e.target.classList.contains('components-layer')) {
                this.selectComponent(null);
            }
        });
    }
    
    async addComponent(type, x, y) {
        const name = this.getComponentName(type);
        
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/components`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: type,
                    name: name,
                    x: x,
                    y: y,
                    config: {}
                })
            });
            
            const data = await response.json();
            const componentId = data.component_id;
            
            // Create visual component
            this.createVisualComponent({
                id: componentId,
                type: type,
                name: name,
                x: x,
                y: y,
                config: {}
            });
            
            this.showToast(`Added ${name}`);
            
        } catch (error) {
            this.showToast('Failed to add component', 'error');
        }
    }
    
    createVisualComponent(data) {
        const container = document.getElementById('components');
        
        const element = document.createElement('div');
        element.className = `visual-component ${data.type}`;
        element.id = `component-${data.id}`;
        element.style.left = `${data.x}px`;
        element.style.top = `${data.y}px`;
        
        element.innerHTML = `
            <div class="component-header">
                <span class="component-icon">${this.getComponentIcon(data.type)}</span>
                <span class="component-name">${data.name}</span>
            </div>
            <div class="component-ports">
                <div class="port input" data-component="${data.id}" data-type="input"></div>
                <div class="port output" data-component="${data.id}" data-type="output"></div>
            </div>
        `;
        
        container.appendChild(element);
        
        // Store component data
        this.components.set(data.id, {
            element: element,
            data: data
        });
        
        // Make draggable
        this.makeDraggable(element, data.id);
        
        // Click to select
        element.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectComponent(data.id);
        });
        
        // Port connections
        element.querySelectorAll('.port').forEach(port => {
            port.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handlePortClick(port);
            });
        });
    }
    
    makeDraggable(element, componentId) {
        let isDragging = false;
        let startX, startY, initialX, initialY;
        
        element.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('port')) return;
            
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = element.getBoundingClientRect();
            const canvas = document.getElementById('canvas').getBoundingClientRect();
            initialX = rect.left - canvas.left;
            initialY = rect.top - canvas.top;
            
            element.style.cursor = 'grabbing';
            element.style.zIndex = 1000;
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            element.style.left = `${initialX + dx}px`;
            element.style.top = `${initialY + dy}px`;
            
            // Update connections
            this.updateConnections();
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                element.style.cursor = 'move';
                element.style.zIndex = '';
                
                // Update component position
                const component = this.components.get(componentId);
                if (component) {
                    component.data.x = parseInt(element.style.left);
                    component.data.y = parseInt(element.style.top);
                }
            }
        });
    }
    
    handlePortClick(port) {
        const componentId = port.dataset.component;
        const portType = port.dataset.type;
        
        if (!this.isConnecting) {
            // Start connection
            if (portType === 'output') {
                this.isConnecting = true;
                this.connectionStart = {
                    componentId: componentId,
                    port: port
                };
                port.style.background = '#22c55e';
            }
        } else {
            // Complete connection
            if (portType === 'input' && componentId !== this.connectionStart.componentId) {
                this.createConnection(
                    this.connectionStart.componentId,
                    componentId
                );
                
                // Reset
                this.connectionStart.port.style.background = '';
                this.isConnecting = false;
                this.connectionStart = null;
            } else {
                // Cancel connection
                this.connectionStart.port.style.background = '';
                this.isConnecting = false;
                this.connectionStart = null;
            }
        }
    }
    
    async createConnection(sourceId, targetId) {
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/connections`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_id: sourceId,
                    target_id: targetId
                })
            });
            
            const data = await response.json();
            
            // Draw connection
            this.drawConnection(sourceId, targetId, data.connection_id);
            
            this.showToast('Connected components');
            
        } catch (error) {
            this.showToast('Failed to create connection', 'error');
        }
    }
    
    drawConnection(sourceId, targetId, connectionId) {
        const svg = document.getElementById('connections');
        const sourceComp = this.components.get(sourceId);
        const targetComp = this.components.get(targetId);
        
        if (!sourceComp || !targetComp) return;
        
        const sourcePort = sourceComp.element.querySelector('.port.output');
        const targetPort = targetComp.element.querySelector('.port.input');
        
        const sourceRect = sourcePort.getBoundingClientRect();
        const targetRect = targetPort.getBoundingClientRect();
        const canvasRect = svg.getBoundingClientRect();
        
        const x1 = sourceRect.left + sourceRect.width / 2 - canvasRect.left;
        const y1 = sourceRect.top + sourceRect.height / 2 - canvasRect.top;
        const x2 = targetRect.left + targetRect.width / 2 - canvasRect.left;
        const y2 = targetRect.top + targetRect.height / 2 - canvasRect.top;
        
        // Create curved path
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = this.getCurvedPath(x1, y1, x2, y2);
        path.setAttribute('d', d);
        path.setAttribute('class', 'connection');
        path.setAttribute('id', `connection-${connectionId}`);
        
        svg.appendChild(path);
        
        this.connections.push({
            id: connectionId,
            sourceId: sourceId,
            targetId: targetId,
            path: path
        });
    }
    
    getCurvedPath(x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const ctrl1x = x1 + dx * 0.5;
        const ctrl1y = y1;
        const ctrl2x = x2 - dx * 0.5;
        const ctrl2y = y2;
        
        return `M ${x1} ${y1} C ${ctrl1x} ${ctrl1y}, ${ctrl2x} ${ctrl2y}, ${x2} ${y2}`;
    }
    
    updateConnections() {
        const svg = document.getElementById('connections');
        const canvasRect = svg.getBoundingClientRect();
        
        this.connections.forEach(conn => {
            const sourceComp = this.components.get(conn.sourceId);
            const targetComp = this.components.get(conn.targetId);
            
            if (sourceComp && targetComp) {
                const sourcePort = sourceComp.element.querySelector('.port.output');
                const targetPort = targetComp.element.querySelector('.port.input');
                
                const sourceRect = sourcePort.getBoundingClientRect();
                const targetRect = targetPort.getBoundingClientRect();
                
                const x1 = sourceRect.left + sourceRect.width / 2 - canvasRect.left;
                const y1 = sourceRect.top + sourceRect.height / 2 - canvasRect.top;
                const x2 = targetRect.left + targetRect.width / 2 - canvasRect.left;
                const y2 = targetRect.top + targetRect.height / 2 - canvasRect.top;
                
                const d = this.getCurvedPath(x1, y1, x2, y2);
                conn.path.setAttribute('d', d);
            }
        });
    }
    
    selectComponent(componentId) {
        // Clear previous selection
        document.querySelectorAll('.visual-component').forEach(comp => {
            comp.classList.remove('selected');
        });
        
        if (componentId) {
            const component = this.components.get(componentId);
            if (component) {
                component.element.classList.add('selected');
                this.showProperties(component.data);
            }
        } else {
            this.showProperties(null);
        }
        
        this.selectedComponent = componentId;
    }
    
    showProperties(componentData) {
        const container = document.getElementById('properties-content');
        
        if (!componentData) {
            container.innerHTML = '<p class="placeholder">Select a component to edit properties</p>';
            return;
        }
        
        let html = '';
        
        // Basic properties
        html += `
            <div class="property-group">
                <label>Name</label>
                <input type="text" id="prop-name" value="${componentData.name}">
            </div>
        `;
        
        // Type-specific properties
        if (componentData.type === 'config') {
            html += this.getConfigProperties(componentData.config);
        } else if (componentData.type === 'agent') {
            html += this.getAgentProperties(componentData.config);
        }
        
        container.innerHTML = html;
        
        // Add change listeners
        container.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('change', () => {
                this.updateComponentProperties();
            });
        });
    }
    
    getConfigProperties(config) {
        return `
            <div class="property-group">
                <label>Model</label>
                <select id="prop-model">
                    <option value="gpt-4" ${config.model === 'gpt-4' ? 'selected' : ''}>GPT-4</option>
                    <option value="gpt-3.5-turbo" ${config.model === 'gpt-3.5-turbo' ? 'selected' : ''}>GPT-3.5 Turbo</option>
                    <option value="claude-3-opus-20240229" ${config.model === 'claude-3-opus-20240229' ? 'selected' : ''}>Claude 3 Opus</option>
                </select>
            </div>
            <div class="property-group">
                <label>Team Size (Research Team)</label>
                <input type="number" id="prop-size" value="${config.size || 5}" min="3" max="10">
            </div>
            <div class="property-group">
                <label>Review Depth (Code Review)</label>
                <select id="prop-depth">
                    <option value="quick" ${config.review_depth === 'quick' ? 'selected' : ''}>Quick</option>
                    <option value="standard" ${config.review_depth === 'standard' ? 'selected' : ''}>Standard</option>
                    <option value="comprehensive" ${config.review_depth === 'comprehensive' ? 'selected' : ''}>Comprehensive</option>
                </select>
            </div>
        `;
    }
    
    getAgentProperties(config) {
        return `
            <div class="property-group">
                <label>Role</label>
                <input type="text" id="prop-role" value="${config.role || ''}">
            </div>
            <div class="property-group">
                <label>Specialty</label>
                <input type="text" id="prop-specialty" value="${config.specialty || ''}">
            </div>
        `;
    }
    
    updateComponentProperties() {
        if (!this.selectedComponent) return;
        
        const component = this.components.get(this.selectedComponent);
        if (!component) return;
        
        // Update name
        const nameInput = document.getElementById('prop-name');
        if (nameInput) {
            component.data.name = nameInput.value;
            component.element.querySelector('.component-name').textContent = nameInput.value;
        }
        
        // Update config
        const updates = {};
        
        ['model', 'size', 'depth', 'role', 'specialty'].forEach(prop => {
            const input = document.getElementById(`prop-${prop}`);
            if (input) {
                updates[prop] = input.value;
            }
        });
        
        Object.assign(component.data.config, updates);
    }
    
    async loadTemplate(templateId) {
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/load-template/${templateId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                // Clear current workflow
                this.clearWorkflow();
                
                // Load template components
                await this.refreshWorkflow();
                
                this.showToast(`Loaded ${templateId.replace('_', ' ')} template`);
            }
        } catch (error) {
            this.showToast('Failed to load template', 'error');
        }
    }
    
    clearWorkflow() {
        // Clear visual components
        document.getElementById('components').innerHTML = '';
        document.getElementById('connections').innerHTML = '';
        
        // Clear data
        this.components.clear();
        this.connections = [];
        this.selectedComponent = null;
    }
    
    async refreshWorkflow() {
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}`);
            const data = await response.json();
            
            // Create components
            data.components.forEach(comp => {
                this.createVisualComponent({
                    id: comp.id,
                    type: comp.type,
                    name: comp.name,
                    x: comp.position.x,
                    y: comp.position.y,
                    config: comp.config
                });
            });
            
            // Create connections
            data.connections.forEach(conn => {
                this.drawConnection(conn.source_id, conn.target_id, conn.id);
            });
            
        } catch (error) {
            this.showToast('Failed to refresh workflow', 'error');
        }
    }
    
    async exportWorkflow() {
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: 'python'
                })
            });
            
            const data = await response.json();
            
            // Show code in modal
            document.getElementById('exportedCode').textContent = data.code;
            this.showModal('exportModal');
            
        } catch (error) {
            this.showToast('Failed to export workflow', 'error');
        }
    }
    
    async saveWorkflow() {
        const name = prompt('Enter workflow name:') || 'workflow';
        
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/save?name=${name}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showToast('Workflow saved successfully');
            }
        } catch (error) {
            this.showToast('Failed to save workflow', 'error');
        }
    }
    
    async showLoadModal() {
        try {
            const response = await fetch('/api/saved-workflows');
            const data = await response.json();
            
            const container = document.getElementById('savedWorkflows');
            container.innerHTML = '';
            
            if (data.workflows.length === 0) {
                container.innerHTML = '<p class="placeholder">No saved workflows</p>';
            } else {
                data.workflows.forEach(workflow => {
                    const item = document.createElement('div');
                    item.className = 'workflow-item';
                    item.innerHTML = `
                        <h3>${workflow.filename}</h3>
                        <p>${workflow.components_count} components, ${workflow.connections_count} connections</p>
                    `;
                    item.addEventListener('click', () => {
                        this.loadWorkflow(workflow.filename);
                    });
                    container.appendChild(item);
                });
            }
            
            this.showModal('loadModal');
            
        } catch (error) {
            this.showToast('Failed to load saved workflows', 'error');
        }
    }
    
    async loadWorkflow(filename) {
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/load/${filename}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.clearWorkflow();
                await this.refreshWorkflow();
                this.hideModal('loadModal');
                this.showToast('Workflow loaded successfully');
            }
        } catch (error) {
            this.showToast('Failed to load workflow', 'error');
        }
    }
    
    copyCode() {
        const code = document.getElementById('exportedCode').textContent;
        navigator.clipboard.writeText(code).then(() => {
            this.showToast('Code copied to clipboard');
        });
    }
    
    async downloadCode() {
        try {
            const response = await fetch(`/api/workflows/${this.workflowId}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: 'python'
                })
            });
            
            const data = await response.json();
            
            // Create download link
            const blob = new Blob([data.code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename;
            a.click();
            URL.revokeObjectURL(url);
            
            this.showToast('Code downloaded');
            
        } catch (error) {
            this.showToast('Failed to download code', 'error');
        }
    }
    
    getComponentName(type) {
        const names = {
            input: 'Input',
            agent: 'Agent',
            workflow: 'Workflow',
            output: 'Output',
            config: 'Configuration'
        };
        return names[type] || 'Component';
    }
    
    getComponentIcon(type) {
        const icons = {
            input: '📥',
            agent: '🤖',
            workflow: '🔄',
            output: '📤',
            config: '⚙️'
        };
        return icons[type] || '📦';
    }
    
    showModal(modalId) {
        document.getElementById(modalId).classList.add('show');
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
    }
    
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VisualBuilder();
});
