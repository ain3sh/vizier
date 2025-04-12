import { ReactElement } from 'react';
import { SendHorizonal } from 'lucide-react';
import QueryBar from '../../../components/querybar/querybar';


function Query() {
    const queryItems: [string, ReactElement][] = [
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." />],
        ['Filter', <input type="text" className="filter-input" placeholder="Filter by..." />],
        ['Enter', <SendHorizonal/>],
    ];
    
    
    return (
            <div>
                {/* Placeholder for query bar content */}
                <QueryBar li={queryItems} />
            </div>
        );
};



export default Query;