import './App.css';
import Header from './Header';
import Wid from './Wid';
import Expand from './Expand';
function App() {
  return (
    
    <div>
      <Header/>
      <div className="px-4 py-5 my-5 text-center">
        <img
          className="d-block mx-auto mb-4"
          src="ChatGPT Image Jul 25, 2025, 03_47_35 PM.png"
          alt=""
          width="200"
          height="200"
        />
        <div className="col-lg-6 mx-auto" >
          <p className="lead mb-4">
             Empowering individuals with the knowledge and confidence to handle heart-related emergencies swiftly and effectively.</p>

        </div>
      </div>
      <Expand/>
      <Wid />
    </div>
  );
}

export default App;
