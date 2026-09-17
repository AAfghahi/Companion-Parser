// MTG Tournament Tracker - Google Apps Script Backend
// Deploy as a web app and use the URL in the HTML tracker

const SHEET_NAME = 'MTG Standings';

// Initialize the spreadsheet
function initializeSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(['Name', 'Record', 'Points', 'Week', 'OMW', 'Store', 'Timestamp']);
  }

  return sheet;
}

// Handle GET requests (for loading data)
function doGet(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const params = e && e.parameter ? e.parameter : {};

  // If season parameter is provided, read from that sheet
  if (params.season) {
    const seasonName = params.season;
    const sheet = ss.getSheetByName(seasonName);

    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        message: 'Season not found: ' + seasonName
      })).setMimeType(ContentService.MimeType.JSON);
    }

    const data = sheet.getDataRange().getValues();
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // If listSeasons parameter is provided, return all sheet names
  if (params.listSeasons) {
    const sheets = ss.getSheets();
    const seasonNames = sheets.map(sheet => sheet.getName());

    return ContentService.createTextOutput(JSON.stringify(seasonNames))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Default: read from current season sheet (MTG Standings)
  const sheet = initializeSheet();
  const data = sheet.getDataRange().getValues();

  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

// Handle POST requests (for appending data)
function doPost(e) {
  try {
    const sheet = initializeSheet();
    const payload = JSON.parse(e.postData.contents);

    if (payload.action === 'append') {
      // Append new rows
      const rows = payload.data;
      rows.forEach(row => {
        sheet.appendRow([
          row.name || '',
          row.record || '',
          row.points || 0,
          row.week || '',
          row.omw || '',
          row.store || '',
          new Date().toISOString()
        ]);
      });

      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: 'Data imported: ' + rows.length + ' entries'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    if (payload.action === 'clear') {
      // Clear all data (keep headers)
      if (sheet.getMaxRows() > 1) {
        sheet.deleteRows(2, sheet.getMaxRows() - 1);
      }
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: 'Sheet cleared'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      message: 'Unknown action'
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
