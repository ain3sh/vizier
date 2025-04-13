import React, { useState, useEffect } from 'react';

interface Stage {
  id: string;
  name: string;
  description: string;
}

interface QueryProgressBarProps {
  currentStage: string | null;
  stages: Stage[];
}

const QueryProgressBar: React.FC<QueryProgressBarProps> = ({ currentStage, stages }) => {
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    if (!currentStage) {
      setProgress(0);
      return;
    }
    
    const currentIndex = stages.findIndex(stage => stage.id === currentStage);
    if (currentIndex >= 0) {
      const progressPercent = (currentIndex / (stages.length - 1)) * 100;
      setProgress(progressPercent);
    }
  }, [currentStage, stages]);
  
  return (
    <div className="query-progress">
      <div className="progress-stages">
        {stages.map((stage, index) => (
          <div 
            key={stage.id}
            className={`progress-stage ${currentStage === stage.id ? 'active' : ''} 
                      ${stages.findIndex(s => s.id === currentStage) > index ? 'completed' : ''}`}
            title={stage.description}
          >
            {stage.name}
          </div>
        ))}
      </div>
      <div className="progress-bar">
        <div 
          className="progress-bar-fill" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>
    </div>
  );
};

export default QueryProgressBar;