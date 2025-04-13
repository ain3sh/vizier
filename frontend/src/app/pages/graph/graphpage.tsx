import AgentFlowGraph from './graph';
import GraphOverlay from './graphoverlay';
import './graph.css';

function GraphPage() {
    return (
        <div className="graph-page">
            <AgentFlowGraph />
            <GraphOverlay />
            <div className="graph-instructions">
                Press Enter to step through the visualization
                {sessionStorage.getItem('graphToDraft') === 'true' && (
                    <div className="draft-instruction">
                        Complete the visualization to proceed to draft review
                    </div>
                )}
            </div>
        </div>
    );
}

export default GraphPage;