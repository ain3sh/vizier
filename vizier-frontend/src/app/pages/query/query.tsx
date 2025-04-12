import { ReactElement, useState } from 'react';
import { Textfit } from 'react-textfit';
import { CircleStop, SendHorizonal } from 'lucide-react';
import axios from 'axios';
import QueryBar from '../../../components/querybar/querybar';

import './query.css';

function Query() {
    const [searchValue, setSearchValue] = useState(''); // State to track the input value
    const [showOverlay, setOverlay] = useState(false); // State to track the expanding animation
    const [responseData, setResponseData] = useState('Please wait while we process your request.'); // State to store API response

    const handleSend = async () => {
        if (searchValue.trim() === '') {
            return; // Empty input, do nothing
        }
        
        console.log('Send button pressed with input:', searchValue);
        setOverlay(true); // Trigger the expanding animation

        // set overlay-title as query text
        const overlayTitle = document.querySelector('.overlay-title') as HTMLElement;
        if (overlayTitle) {
            overlayTitle.textContent = searchValue;
        }
        
        try {
            // Make POST request with searchValue
            const response = await axios.post('https://api.example.com/query', {
                query: searchValue
            });
            
            console.log('POST response:', response.data);
            
            // After successful POST, fetch the results
            fetchResults(response.data.id || 'default-id');
        } catch (error) {
            console.error('Error sending query:', error);
            setResponseData('Error processing your request. Please try again.');
        }
        
        setSearchValue(''); // Clear input field
    };
    
    const fetchResults = async (queryId: string) => {
        try {
            // Simulate delay for showing loading state
            setResponseData('Fetching results...');
            
            // Make GET request to fetch results
            const response = await axios.get(`https://api.example.com/results/${queryId}`);
            
            console.log('GET response:', response.data);
            
            // Update the overlay text with the response
            setResponseData(response.data.result || 'No results found.');
        } catch (error) {
            console.error('Error fetching results:', error);
            setResponseData('Error retrieving results. Please try again.');
        }
    };

    const handleStop = () => {
        // Add this line to ensure the animation has time to complete
        const fadeContainer = document.querySelector('.fade-container') as HTMLElement;
        if (fadeContainer) {
            fadeContainer.style.transition = 'all 0.5s ease-in-out';
        }
        setOverlay(false); // Reset the overlay state when Stop is clicked
        setResponseData('Please wait while we process your request.'); // Reset response text
    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchValue(event.target.value); // Update the state with the input value
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSend(); // Trigger the send action on Enter press
        }
    };

    const queryItems: [string, ReactElement][] = [
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={handleSearchChange} onKeyDown={handleKeyDown}/>],
        ['Stop', <CircleStop size={40} className="stop-btn" onClick={handleStop}/>],
        ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend}/>],
    ];

    return (
        <div>
            {/* Overlay container */}
            <div className={`fade-container ${showOverlay ? 'overlay' : ''}`}>
                <div className={`overlay-content ${showOverlay ? 'visible' : ''}`}>
                    <Textfit 
                        mode="multi"
                        min={12}
                        max={48}
                        style={{
                            height: '100%',
                            width: '80%',
                            overflow: 'hidden',
                            wordWrap: 'break-word',
                            whiteSpace: 'pre-wrap'
                        }}
                    >
                        <p className="overlay-title"></p>
                    </Textfit>
                    <p className="overlay-text">{responseData}</p>
                </div>
            </div>

            {/* QueryBar container */}
            <div className={`query-bar-container ${showOverlay ? 'moved' : ''}`}>
                <QueryBar li={queryItems} />
            </div>
        </div>
    );
}

export default Query;