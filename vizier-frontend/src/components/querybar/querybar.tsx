import React, { ReactElement } from "react";
import './querybar.css';

interface QueryBarProps {
    li: [string, ReactElement][];
}

const QueryBar: React.FC<QueryBarProps> = ({ li }) => {
    return (
        <div className="querybar-container">
            {li.map((item, index) => (
                <div className="querybar-item" key={index}>
                    {item[1]} {/* Render the icon */}
                    <span>{item[0]}</span> {/* Render the label (hidden by CSS) */}
                </div>
            ))}
        </div>
    );
};

export default QueryBar;