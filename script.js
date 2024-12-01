const form = document.getElementById('dataForm');
const textInput = document.getElementById('textInput');
const submitButton = document.getElementById('submitButton');
const stopButton = document.getElementById('stopButton');
const responseMessage = document.getElementById('responseMessage');

const host_url = host_url_main; // 'http://localhost:8080';
const update_interval_msec = update_interval;

// Function to post form data
async function postData() 
{
  const inputValue = textInput.value;

  // Prepare data to send
  const jsonData = 
  {
    text: inputValue
  };

  try 
  {
    const response = await fetch(host_url+'/submit', 
                                  {
                                    method: 'POST',
                                    headers: {
                                      'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify(jsonData),
                                  });

    if (!response.ok) 
    {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const result = await response.json();
    // responseMessage.textContent = `Success: ${result.message}`;
  } 
  catch (error) 
  {
    console.error('Error posting data:', error);
    responseMessage.textContent = 'Error submitting data.';
  }
}

async function postStopRequest() 
{
  // Prepare data to send
  const jsonData = 
  {
    text: ''
  };

  try 
  {
    const response = await fetch(host_url+'/requeststop', 
                                  {
                                    method: 'POST',
                                    headers: {
                                      'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify(jsonData),
                                  });

    if (!response.ok) 
    {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const result = await response.json();
    // responseMessage.textContent = `${result.stoprequests}`;
  } 
  catch (error) 
  {
    console.error('Error posting data:', error);
    responseMessage.textContent = 'Error submitting data: '+error;
  }

}

async function updateStops()
{
  // Prepare data to send
  const jsonData = 
  {
    text: ''
  };
  const response = await fetch(host_url+'/stopdata', 
                                {
                                  method: 'POST',
                                  headers: {
                                    'Content-Type': 'application/json',
                                    'Access-Control-Allow-Origin': '*',
                                  },
                                  body: JSON.stringify(jsonData),
                                });

  const result = await response.json();
  // console.log(result.stoprequests.length)
  if (result.stoprequests.length!=0)
  {  
    responseMessage.textContent = `IDs that have voted: ${result.stoprequests}`;
  }
  else
  {
    responseMessage.textContent = ''; 
  }
}

// Add event listeners to the buttons
// submitButton.addEventListener('click', postData);
stopButton.addEventListener('click', postStopRequest);

// update every 500 msec
setInterval(updateStops, update_interval_msec)
