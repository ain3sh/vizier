import { useState, useEffect, useCallback, useRef } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState } from '@xyflow/react';

import '@xyflow/react/dist/style.css';
import './graph.css';

const agents = ['agent-1', 'agent-2', 'agent-3', 'agent-4'];
const steps = ['A', 'B', 'C', 'D'];

const allNodesData = [
  { id: 'query-root', data: {}, position: { x: 400, y: 50 } },
  ...agents.flatMap((agentId, i) => {
    const x = 150 + i * 250;
    return [
      { id: agentId, data: {}, position: { x, y: 150 } },
      ...steps.map((step, j) => ({
        id: `${agentId}-${step}`,
        data: {},
        position: { x, y: 250 + j * 200 },
      })),
    ];
  }),
];

const allEdgesData = [
  ...agents.map(agentId => ({ id: `query-${agentId}`, source: 'query-root', target: agentId })),
  ...agents.flatMap(agentId => (
    steps.slice(0, -1).map((step, i) => ({
      id: `${agentId}-${step}-${steps[i + 1]}`,
      source: `${agentId}-${step}`,
      target: `${agentId}-${steps[i + 1]}`,
    })).concat({
      id: `${agentId}-link`, source: agentId, target: `${agentId}-A`
    })
  )),
];

const simulationSteps = [
  { addNodes: ['query-root'], addEdges: [], activeNode: 'query-root' },
  { addNodes: agents, addEdges: agents.map(a => `query-${a}`), activeNode: null },
  { addNodes: ['agent-2-A'], addEdges: ['agent-2-link'], activeNode: 'agent-2-A' },
  { addNodes: ['agent-4-A'], addEdges: ['agent-4-link'], activeNode: 'agent-4-A' },
  { addNodes: ['agent-1-A'], addEdges: ['agent-1-link'], activeNode: 'agent-1-A' },
  { addNodes: ['agent-3-A'], addEdges: ['agent-3-link'], activeNode: 'agent-3-A' },
  { addNodes: ['agent-3-B'], addEdges: ['agent-3-A-B'], activeNode: 'agent-3-B' },
  { addNodes: ['agent-1-B'], addEdges: ['agent-1-A-B'], activeNode: 'agent-1-B' },
  { addNodes: ['agent-4-B'], addEdges: ['agent-4-A-B'], activeNode: 'agent-4-B' },
  { addNodes: ['agent-2-B'], addEdges: ['agent-2-A-B'], activeNode: 'agent-2-B' },
  { addNodes: ['agent-1-C'], addEdges: ['agent-1-B-C'], activeNode: 'agent-1-C' },
  { addNodes: ['agent-2-C'], addEdges: ['agent-2-B-C'], activeNode: 'agent-2-C' },
  { addNodes: ['agent-1-D'], addEdges: ['agent-1-C-D'], activeNode: 'agent-1-D' },
  { addNodes: ['agent-2-D'], markFailed: ['agent-2-D'], activeNode: 'agent-2-D' },
  { addNodes: ['agent-3-C'], markFailed: ['agent-3-C'], activeNode: 'agent-3-C' },
  { addNodes: ['agent-4-C'], markFailed: ['agent-4-C'], activeNode: 'agent-4-C' },
];

function AgentFlowGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);

  const applyTemporaryClass = useCallback((ids, type, className, duration = 1500) => {
    const update = type === 'node' ? setNodes : setEdges;
    update(elements => elements.map(el => ids.includes(el.id) ? { ...el, className: `${el.className || ''} ${className}`.trim() } : el));
    setTimeout(() => {
      update(elements => elements.map(el => ids.includes(el.id) ? { ...el, className: (el.className || '').replace(className, '').trim() } : el));
    }, duration);
  }, [setNodes, setEdges]);

  useEffect(() => {
    if (currentStepIndex >= simulationSteps.length) return;

    const timer = setTimeout(() => {
      if (currentStepIndex < 0) {
        setCurrentStepIndex(0);
        return;
      }

      const step = simulationSteps[currentStepIndex];

      if (step.markFailed) {
        setNodes(prev => prev.map(n => step.markFailed.includes(n.id)
          ? { ...n, style: { background: '#444', borderColor: '#999', borderRadius: '999px' } }
          : n
        ));
        setCurrentStepIndex(i => i + 1);
        return;
      }

      const newNodes = (step.addNodes || []).map(id => allNodesData.find(n => n.id === id)).filter(Boolean);
      const newEdges = (step.addEdges || []).map(id => allEdgesData.find(e => e.id === id)).filter(Boolean);

      setNodes(prev => {
        const updated = prev.map(n => ({
          ...n,
          className: (n.className || '').replace('node-pulsing', '').trim(),
          style: { ...n.style, borderRadius: '999px' },
        }));

        const active = updated.find(n => n.id === step.activeNode);
        const others = updated.filter(n => n.id !== step.activeNode);

        const activeNode = active ? {
          ...active,
          className: `${active.className || ''} node-pulsing`.trim(),
          style: {
            ...(active.style || {}),
            background: 'rgb(0, 168, 76)',
            borderColor: 'rgb(0, 168, 76)',
            borderRadius: '999px'
          }
        } : null;

        const added = newNodes.map(n => ({
          ...n,
          className: n.id === step.activeNode ? 'node-pulsing' : '',
          style: { borderRadius: '999px' }
        }));

        return [...others, ...(activeNode ? [activeNode] : []), ...added];
      });

      setEdges(prev => {
        const newUnique = newEdges.filter(e => !prev.some(pe => pe.id === e.id));
        const newSources = newUnique.map(e => e.source);

        setNodes(nodes => nodes.map(n =>
        newSources.includes(n.id)
            ? {
                ...n,
                className: (n.className || '').replace('node-pulsing', '').trim(),
                style: {
                ...(n.style || {}),
                background: '#e5e7eb',
                borderColor: '#d1d5db',
                }
            }
            : n
        ));

        return [...prev, ...newUnique];
      });

      if ((step.addNodes || []).length > 0) applyTemporaryClass(step.addNodes, 'node', 'node-glowing', 3000);
      if ((step.addEdges || []).length > 0) applyTemporaryClass(step.addEdges, 'edge', 'edge-glowing', 4000);

      setCurrentStepIndex(i => i + 1);
    }, 3000);

    return () => clearTimeout(timer);
  }, [currentStepIndex, applyTemporaryClass]);

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Controls />
        <Background color="#000000" variant="lines" />
      </ReactFlow>
    </div>
  );
}

export default AgentFlowGraph;
