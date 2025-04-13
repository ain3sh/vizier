import { useState, useEffect, useCallback } from 'react';
import { ReactFlow, useNodesState, useEdgesState, Node, Edge } from '@xyflow/react';
import { useNavigate } from 'react-router-dom';

import '@xyflow/react/dist/style.css';
import './graph.css';

interface NodeData extends Record<string, unknown> {
  label?: string;
}

type NodeType = Node<NodeData>;
type EdgeType = Edge;

interface NodeDefinition {
  id: string;
  data: NodeData;
  position: { x: number; y: number };
  className?: string;
  style?: React.CSSProperties;
}

interface SimulationStep {
  addNodes: string[];
  addEdges?: string[];
  activeNode: string | null;
  markFailed?: string[];
}

const agents = ['agent-1', 'agent-2', 'agent-3', 'agent-4'];
const steps = ['A', 'B', 'C', 'D'];

const allNodesData: NodeDefinition[] = [
  { id: 'initial-node', data: { label: 'Start' }, position: { x: 400, y: 0 } },
  { id: 'query-root', data: { label: 'Query' }, position: { x: 400, y: 200 } },
  ...agents.flatMap((agentId, i) => {
    const x = 150 + i * 250;
    return [
      { id: agentId, data: { label: agentId }, position: { x, y: 400 } },
      ...steps.map((step, j) => ({
        id: `${agentId}-${step}`,
        data: { label: `${step}` },
        position: { x, y: 600 + j * 200 },
      })),
    ];
  }),
];

const allEdgesData: EdgeType[] = [
  { id: 'initial-to-query', source: 'initial-node', target: 'query-root', type: 'default' },
  ...agents.map(agentId => ({ 
    id: `query-${agentId}`, 
    source: 'query-root', 
    target: agentId, 
    type: 'default' 
  })),
  ...agents.flatMap(agentId => (
    steps.slice(0, -1).map((step, i) => ({
      id: `${agentId}-${step}-${steps[i + 1]}`,
      source: `${agentId}-${step}`,
      target: `${agentId}-${steps[i + 1]}`,
      type: 'default'
    })).concat({
      id: `${agentId}-link`, 
      source: agentId, 
      target: `${agentId}-A`, 
      type: 'default'
    })
  )),
];

const simulationSteps: SimulationStep[] = [
  { addNodes: ['initial-node'], addEdges: [], activeNode: 'initial-node' },
  { addNodes: ['query-root'], addEdges: ['initial-to-query'], activeNode: 'query-root' },
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
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([] as NodeType[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as EdgeType[]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);

  const applyTemporaryClass = useCallback((ids: string[], type: 'node' | 'edge', className: string, duration = 1500) => {
    if (type === 'node') {
      setNodes(elements => 
        elements.map(el => ids.includes(el.id) ? 
          { ...el, className: `${el.className || ''} ${className}`.trim() } : el
        )
      );
      setTimeout(() => {
        setNodes(elements => 
          elements.map(el => ids.includes(el.id) ? 
            { ...el, className: (el.className || '').replace(className, '').trim() } : el
          )
        );
      }, duration);
    } else {
      setEdges(elements => 
        elements.map(el => ids.includes(el.id) ? 
          { ...el, className: `${el.className || ''} ${className}`.trim() } : el
        )
      );
      setTimeout(() => {
        setEdges(elements => 
          elements.map(el => ids.includes(el.id) ? 
            { ...el, className: (el.className || '').replace(className, '').trim() } : el
          )
        );
      }, duration);
    }
  }, [setNodes, setEdges]);

  const stepSimulation = useCallback(() => {
    if (currentStepIndex >= simulationSteps.length - 1) return;
    const nextStepIndex = currentStepIndex + 1;
    const step = simulationSteps[nextStepIndex];

    if (step.markFailed) {
      setNodes((prev: NodeType[]) => prev.map(n => step.markFailed!.includes(n.id)
        ? { ...n, style: { ...n.style, background: '#444', borderColor: '#999', borderRadius: '999px' } }
        : n
      ));
      setCurrentStepIndex(nextStepIndex);
      return;
    }

    const newNodes = (step.addNodes || [])
      .map(id => allNodesData.find(n => n.id === id))
      .filter(Boolean)
      .map(n => ({ ...n, type: 'default' } as NodeType));

    const newEdges = (step.addEdges || [])
      .map(id => allEdgesData.find(e => e.id === id))
      .filter(Boolean) as EdgeType[];

    setNodes((prev: NodeType[]) => {
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

      return [...others, ...(activeNode ? [activeNode] : []), ...newNodes];
    });

    setEdges((prev: EdgeType[]) => {
      const newUnique = newEdges.filter(e => !prev.some(pe => pe.id === e.id));
      const newSources = newUnique.map(e => e.source);

      setNodes((nodes: NodeType[]) => nodes.map(n =>
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

    if (step.addNodes.length > 0) applyTemporaryClass(step.addNodes, 'node', 'node-glowing', 3000);
    if (step.addEdges && step.addEdges.length > 0) {
      applyTemporaryClass(step.addEdges, 'edge', 'edge-glowing', 4000);
    }

    setCurrentStepIndex(nextStepIndex);
  }, [currentStepIndex, applyTemporaryClass, setNodes, setEdges]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') stepSimulation();
      if (e.key.toLowerCase() === 'q') {
        navigate('/', { replace: true }); // Using replace to make it a temporary redirect
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [stepSimulation, navigate]);

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
      </ReactFlow>
    </div>
  );
}

export default AgentFlowGraph;
