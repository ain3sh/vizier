import AgentFlowGraph from './graph'; // your animated graph
import './graph.css'; // optional styling

export default function AgentFlowGraphOverlay({ visible }: { visible: boolean }) {
  if (!visible) return null;

  return (
    <div className="agent-graph-overlay">
      <AgentFlowGraph />
    </div>
  );
}