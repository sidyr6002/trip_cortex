import { FaPlane } from "react-icons/fa";

export default function FlightPath() {
    return (
        <div className="flex items-center w-full max-w-36">

            {/* Left indicator */}
            <div className="flex items-center flex-1">
                {/* Left Arrowhead */}
                <div className="w-0 h-0 border-y-4 border-y-transparent border-r-[6px] border-r-black"></div>
                {/* Dotted Line */}
                <div className="flex-1 border-b-[3px] border-dotted border-gray-500 h-0 mx-1"></div>
            </div>

            {/* Center Airplane Icon */}
            <div className="px-2 text-primary-600">
                <FaPlane size={20} />
            </div>

            {/* Right indicator */}
            <div className="flex items-center flex-1">
                {/* Dotted Line */}
                <div className="flex-1 border-b-[3px] border-dotted border-gray-500 h-0 mx-1"></div>
                {/* Right Arrowhead */}
                <div className="w-0 h-0 border-y-4 border-y-transparent border-l-[6px] border-l-black"></div>
            </div>

        </div>
    );
}