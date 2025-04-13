import React, { ReactElement } from "react";
import './querybar.css';

interface QueryBarProps {
    li: [string, ReactElement][];
}

const QueryBar: React.FC<QueryBarProps> = ({ li }) => {
    return (
        <div className="querybar-container">
            {li.map((item, index) => (
                <div 
                    className={`querybar-item ${item[0] === 'Search' ? 'querybar-item-grow' : ''}`} 
                    key={index}
                >
                    {item[1]} {/* Render the element */}
                </div>
            ))}
        </div>
    );
};

export default QueryBar;