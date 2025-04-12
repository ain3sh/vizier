import { ReactElement, useState } from 'react';
import { SendHorizonal } from 'lucide-react';
import QueryBar from '../../../components/querybar/querybar';

import './query.css';

function Query() {
    const [searchValue, setSearchValue] = useState(''); // State to track the input value

    const handleSend = () => {
        console.log('Send button pressed with input:', searchValue);
        setSearchValue('');

    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchValue(event.target.value); // Update the state with the input value
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSend(); // Trigger the send action on Enter press
        }
    };

    /* style the ReactElements here in query.css */
    const queryItems: [string, ReactElement][] = [
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={handleSearchChange} onKeyDown={handleKeyDown}/>],
        ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend}/>]
    ];

    return (
        <div>
            <QueryBar li={queryItems} />
        </div>
    );
}

export default Query;