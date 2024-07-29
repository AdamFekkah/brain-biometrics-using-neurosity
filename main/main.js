require('dotenv').config();
const { timer } = require("rxjs");
const { takeUntil } = require("rxjs/operators");
const { Neurosity } = require("@neurosity/sdk");
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const fs = require('fs');
const crypto = require('crypto');

// Initialize the neurosity device
const neurosity = new Neurosity({
  deviceId: process.env.DEVICE_ID
});

// Verify environment variables are loaded
console.log('DEVICE_ID:', process.env.DEVICE_ID);
console.log('EMAIL:', process.env.EMAIL);
console.log('PASSWORD:', process.env.PASSWORD);

const csvWriter = createCsvWriter({
  path: 'neurosity_readings.csv',
  header: [
    {id: 'timestamp', title: 'Timestamp'},
    {id: 'channel', title: 'Channel'},
    {id: 'value', title: 'Value'}
  ]
});

let counter = 0; // Initialize counter
const readings = []; // Array to store all readings

const logReading = async (data) => {
  const records = data.map(d => ({
    timestamp: Date.now(),
    channel: 'Cz', // Example channel, replace with actual channel info
    value: d
  }));

  readings.push(...records);
  console.log('Reading added to the array');
};

const finalizeAndEncryptCsv = async () => {
  await csvWriter.writeRecords(readings);
  console.log('Data written to CSV');
}

const startCapturing = async () => {
  try {
    await neurosity.login({
      email: process.env.EMAIL,
      password: process.env.PASSWORD
    });

    console.log("Logged in!");

    const subscription = neurosity.brainwaves("raw")
      .pipe(
        takeUntil(
          timer(30000) // in milliseconds
        )
      )
      .subscribe(async (brainwaves) => {
        console.log(brainwaves);
        await logReading(brainwaves);
      });

    const handleExit = async () => {
      console.log('Closing subscription and exiting.');
      subscription.unsubscribe();
      await finalizeAndEncryptCsv();
      process.exit();
    };

    setTimeout(handleExit, 30000);

    process.on('SIGINT', handleExit);
    process.on('SIGTERM', handleExit);

  } catch (error) {
    console.error("Error logging in or capturing readings:", error);
  }
};

startCapturing();
