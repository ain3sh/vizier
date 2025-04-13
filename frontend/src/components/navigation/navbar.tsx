import React, { ReactElement, useState } from "react";
import { Menu, Hexagon } from "lucide-react";
import "./navbar.css";

interface NavProps {
    li: [string, ReactElement][];
}

const NavBar: React.FC<NavProps> = ({ li }) => {
    const [window, setWindow] = useState(true);
    const [isRotated, setIsRotated] = useState(true); // Track rotation state

    const openClose = () => {
        setIsRotated(!isRotated); // Toggle rotation state
        setWindow(!window); // Toggle the menu state
    };

    return (
        <nav
            className={`navbar-menu ${window ? "" : "open"}`}
            style={{ width: window ? 80 : 200 }}
        >
            <div className="navbar-logo-box">
                <div className="navbar-logo-icon">
                    <Hexagon size={64} />
                </div>
                <div className="navbar-logo">Vizier</div>
            </div>
            <div className="burger-container">
                <div
                    className="burger"
                    style={{
                        transform: isRotated ? "rotate(0deg)" : "rotate(270deg)", // Apply rotation
                        transition: "transform 0.7s ease", // Smooth rotation
                    }}
                    onClick={() => openClose()}
                >
                    <Menu size={32} />
                </div>
            </div>
            <ul className="navbar-list">
                {li.map((item, i) => (
                    <div className="navbar-li-box" key={i}>
                        <div
                            className="navbar-li-icon"
                            style={{ paddingLeft: 20 }}
                        >
                            {item[1]}
                        </div>
                        <li className="navbar-li">{item[0]}</li>
                    </div>
                ))}
            </ul>
        </nav>
    );
};

export default NavBar;