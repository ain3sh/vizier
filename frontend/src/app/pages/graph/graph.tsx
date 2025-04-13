import { useState, useEffect, useCallback, useRef } from 'react';
import { ReactFlow, useNodesState, useEdgesState, Node, Edge, ReactFlowInstance } from '@xyflow/react';
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

// First phase agents (data retrieval)
const retrievalAgents = ['twitter-agent', 'web-agent'];
const retrievalSteps = ['search', 'analyze', 'summarize'];

// Second phase agents (source processing)
const sourceAgents = ['source-1', 'source-2', 'source-3', 'source-4'];
const sourceSteps = ['read', 'validate', 'analyze', 'extract'];

const allNodesData: NodeDefinition[] = [
  // First phase - Query and Retrieval
  { id: 'start-node', data: { label: 'Start' }, position: { x: 400, y: 0 } },
  { id: 'query-node', data: { label: 'Query' }, position: { x: 400, y: 200 } },
  ...retrievalAgents.flatMap((agentId, i) => {
    const x = 250 + i * 300;
    return [
      { id: agentId, data: { label: agentId }, position: { x, y: 400 } },
      ...retrievalSteps.map((step, j) => ({
        id: `${agentId}-${step}`,
        data: { label: `${step}` },
        position: { x, y: 600 + j * 200 },
      })),
    ];
  }),
  { id: 'merge-node', data: { label: 'Sources Collection' }, position: { x: 400, y: 1200 } },
  
  // Second phase - Source Processing
  ...sourceAgents.flatMap((agentId, i) => {
    const x = 100 + i * 200;
    return [
      { id: agentId, data: { label: agentId }, position: { x, y: 1400 } },
      ...sourceSteps.map((step, j) => ({
        id: `${agentId}-${step}`,
        data: { label: `${step}` },
        position: { x, y: 1600 + j * 200 },
      })),
    ];
  }),
  { id: 'final-merge-node', data: { label: 'Compile & Write' }, position: { x: 400, y: 2400 } },
];

const allEdgesData: EdgeType[] = [
  // Phase 1 edges
  { id: 'start-to-query', source: 'start-node', target: 'query-node', type: 'default' },
  ...retrievalAgents.map(agentId => ({ 
    id: `query-${agentId}`, 
    source: 'query-node', 
    target: agentId, 
    type: 'default' 
  })),
  ...retrievalAgents.flatMap(agentId => (
    retrievalSteps.slice(0, -1).map((step, i) => ({
      id: `${agentId}-${step}-${retrievalSteps[i + 1]}`,
      source: `${agentId}-${step}`,
      target: `${agentId}-${retrievalSteps[i + 1]}`,
      type: 'default'
    })).concat({
      id: `${agentId}-link`, 
      source: agentId, 
      target: `${agentId}-search`, 
      type: 'default'
    })
  )),
  // Connect the last step of each retrieval agent to the merge node
  ...retrievalAgents.map(agentId => ({
    id: `${agentId}-to-merge`,
    source: `${agentId}-summarize`,
    target: 'merge-node',
    type: 'default'
  })),
  
  // Phase 2 edges
  ...sourceAgents.map(agentId => ({
    id: `merge-to-${agentId}`,
    source: 'merge-node',
    target: agentId,
    type: 'default'
  })),
  ...sourceAgents.flatMap(agentId => (
    sourceSteps.slice(0, -1).map((step, i) => ({
      id: `${agentId}-${step}-${sourceSteps[i + 1]}`,
      source: `${agentId}-${step}`,
      target: `${agentId}-${sourceSteps[i + 1]}`,
      type: 'default'
    })).concat({
      id: `${agentId}-source-link`, 
      source: agentId, 
      target: `${agentId}-read`, 
      type: 'default'
    })
  )),
  // Connect the last step of each source agent to the final merge node
  ...sourceAgents.map(agentId => ({
    id: `${agentId}-to-final`,
    source: `${agentId}-extract`,
    target: 'final-merge-node',
    type: 'default'
  })),
];

const simulationSteps: SimulationStep[] = [
  // Phase 1: Retrieval process
  { addNodes: ['start-node'], addEdges: [], activeNode: 'start-node' },
  { addNodes: ['query-node'], addEdges: ['start-to-query'], activeNode: 'query-node' },
  { addNodes: retrievalAgents, addEdges: retrievalAgents.map(a => `query-${a}`), activeNode: null },
  { addNodes: ['twitter-agent-search'], addEdges: ['twitter-agent-link'], activeNode: 'twitter-agent-search' },
  { addNodes: ['web-agent-search'], addEdges: ['web-agent-link'], activeNode: 'web-agent-search' },
  { addNodes: ['twitter-agent-analyze'], addEdges: ['twitter-agent-search-analyze'], activeNode: 'twitter-agent-analyze' },
  { addNodes: ['web-agent-analyze'], addEdges: ['web-agent-search-analyze'], activeNode: 'web-agent-analyze' },
  { addNodes: ['twitter-agent-summarize'], addEdges: ['twitter-agent-analyze-summarize'], activeNode: 'twitter-agent-summarize' },
  { addNodes: ['web-agent-summarize'], addEdges: ['web-agent-analyze-summarize'], activeNode: 'web-agent-summarize' },
  { addNodes: ['merge-node'], addEdges: ['twitter-agent-to-merge', 'web-agent-to-merge'], activeNode: 'merge-node' },
  
  // Phase 2: Source processing
  { addNodes: sourceAgents, addEdges: sourceAgents.map(a => `merge-to-${a}`), activeNode: null },
  
  // Source agent 1 path - completes successfully
  { addNodes: ['source-1-read'], addEdges: ['source-1-source-link'], activeNode: 'source-1-read' },
  { addNodes: ['source-1-validate'], addEdges: ['source-1-read-validate'], activeNode: 'source-1-validate' },
  { addNodes: ['source-1-analyze'], addEdges: ['source-1-validate-analyze'], activeNode: 'source-1-analyze' },
  { addNodes: ['source-1-extract'], addEdges: ['source-1-analyze-extract'], activeNode: 'source-1-extract' },
  
  // Source agent 2 path - completes successfully
  { addNodes: ['source-2-read'], addEdges: ['source-2-source-link'], activeNode: 'source-2-read' },
  { addNodes: ['source-2-validate'], addEdges: ['source-2-read-validate'], activeNode: 'source-2-validate' },
  { addNodes: ['source-2-analyze'], addEdges: ['source-2-validate-analyze'], activeNode: 'source-2-analyze' },
  { addNodes: ['source-2-extract'], addEdges: ['source-2-analyze-extract'], activeNode: 'source-2-extract' },
  
  // Source agent 3 path - rejects at validation step
  { addNodes: ['source-3-read'], addEdges: ['source-3-source-link'], activeNode: 'source-3-read' },
  { addNodes: ['source-3-validate'], addEdges: ['source-3-read-validate'], markFailed: ['source-3-validate'], activeNode: 'source-3-validate' },
  
  // Source agent 4 path - rejects at validation step
  { addNodes: ['source-4-read'], addEdges: ['source-4-source-link'], activeNode: 'source-4-read' },
  { addNodes: ['source-4-validate'], addEdges: ['source-4-read-validate'], markFailed: ['source-4-validate'], activeNode: 'source-4-validate' },
  
  // Final merge
  { addNodes: ['final-merge-node'], addEdges: ['source-1-to-final', 'source-2-to-final'], activeNode: 'final-merge-node' },
];

// Define viewport focus points
const viewportRegions = {
  top: { minY: 0, maxY: 800, center: { x: 400, y: 400 } },
  middle: { minY: 800, maxY: 1600, center: { x: 400, y: 1200 } },
  bottom: { minY: 1600, maxY: 2400, center: { x: 400, y: 2000 } }
};

function determineViewportRegion(nodeId: string): keyof typeof viewportRegions {
  const node = allNodesData.find(n => n.id === nodeId);
  if (!node) return 'middle';
  
  const y = node.position.y;
  if (y <= viewportRegions.top.maxY) return 'top';
  if (y <= viewportRegions.middle.maxY) return 'middle';
  return 'bottom';
}

function AgentFlowGraph() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([] as NodeType[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as EdgeType[]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const flowRef = useRef<ReactFlowInstance | null>(null);
  const [isReturningFromQuery, setIsReturningFromQuery] = useState(false);
  const [graphToDraft, setGraphToDraft] = useState(false);

  const focusOnRegion = useCallback((region: keyof typeof viewportRegions, duration = 800) => {
    if (!flowRef.current) return;
    
    const viewport = viewportRegions[region];
    flowRef.current.setCenter(
      viewport.center.x,
      viewport.center.y,
      { duration, zoom: 0.75 }
    );
  }, []);

  // Add effect to check if this is first time from query
  useEffect(() => {
    const isFirstTime = sessionStorage.getItem('firstTimeGraph');
    const savedGraphState = sessionStorage.getItem('graphState');
    const queryState = sessionStorage.getItem('queryState');

    if (isFirstTime === 'true') {
      // Reset everything
      setNodes([]);
      setEdges([]);
      setCurrentStepIndex(-1);
      sessionStorage.removeItem('graphState');
      sessionStorage.removeItem('firstTimeGraph');
      setIsReturningFromQuery(false);
    } else if (savedGraphState && queryState) {
      const { nodes, edges, currentStepIndex } = JSON.parse(savedGraphState);
      setNodes(nodes);
      setEdges(edges);
      setCurrentStepIndex(currentStepIndex);
      setIsReturningFromQuery(true);
      // Add a small delay to ensure the graph is initialized
      setTimeout(() => focusOnRegion('middle'), 100);
    }
  }, [setNodes, setEdges, focusOnRegion]);

  // Add effect to check for graph to draft transition
  useEffect(() => {
    const graphToDraft = sessionStorage.getItem('graphToDraft');
    if (graphToDraft === 'true') {
      setGraphToDraft(true);
    }
  }, []);

  // Save state before leaving
  useEffect(() => {
    return () => {
      // Only save if we have progress
      if (currentStepIndex > -1) {
        const stateToSave = {
          nodes,
          edges,
          currentStepIndex
        };
        sessionStorage.setItem('graphState', JSON.stringify(stateToSave));
      }
    };
  }, [nodes, edges, currentStepIndex]);

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
    if (currentStepIndex >= simulationSteps.length - 1) {
      if (graphToDraft) {
        // Clean up storage and navigate to draft review
        sessionStorage.removeItem('graphToDraft');
        sessionStorage.removeItem('graphState');
        navigate('/');
      }
      return;
    }
    const nextStepIndex = currentStepIndex + 1;
    const step = simulationSteps[nextStepIndex];

    if (step.markFailed) {
      // First mark all the subsequent nodes in the same path as failed
      const failedNodePaths = step.markFailed.map(nodeId => {
        const [agentId] = nodeId.split('-');
        return sourceSteps
          .map(step => `${agentId}-${step}`)
          .filter(id => {
            const stepIndex = sourceSteps.findIndex(step => id.endsWith(step));
            const failedStepIndex = sourceSteps.findIndex(step => nodeId.endsWith(step));
            return stepIndex >= failedStepIndex;
          });
      }).flat();

      setNodes((prev: NodeType[]) => prev.map(n => 
        failedNodePaths.includes(n.id)
          ? { 
              ...n, 
              data: { 
                ...n.data, 
                failed: true 
              },
              className: 'failed-node',
              style: { 
                ...n.style, 
                background: '#ff4d4d', 
                borderColor: '#ff0000', 
                borderRadius: '999px',
              }
            }
          : n
      ));
      
      // Find the last failed node to focus on
      const lastFailedNode = failedNodePaths[failedNodePaths.length - 1];
      const region = determineViewportRegion(lastFailedNode);
      setTimeout(() => focusOnRegion(region), 100);

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

    if (step.activeNode) {
      const region = determineViewportRegion(step.activeNode);
      setTimeout(() => focusOnRegion(region), 100);
    } else if (step.addNodes.length > 0) {
      // If no active node, focus on the last added node
      const lastAddedNode = step.addNodes[step.addNodes.length - 1];
      const region = determineViewportRegion(lastAddedNode);
      setTimeout(() => focusOnRegion(region), 100);
    }

    setCurrentStepIndex(nextStepIndex);
  }, [currentStepIndex, focusOnRegion, applyTemporaryClass, setNodes, setEdges, graphToDraft, navigate]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') stepSimulation();
      if (e.key.toLowerCase() === 'q') {
        // Clear graph state if explicitly going back to query
        sessionStorage.removeItem('graphState');
        navigate('/', { replace: true });
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
        onInit={(instance) => {
          flowRef.current = instance;
          if (!isReturningFromQuery) {
            focusOnRegion('top');
          }
        }}
        fitView={false}
      >
      </ReactFlow>
    </div>
  );
}

export default AgentFlowGraph;