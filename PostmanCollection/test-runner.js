/**
 * Postman Collection Test Runner
 * 
 * This script can be used with Newman (Postman CLI) to run automated tests
 * against the Smart Parking Management System API.
 * 
 * Installation:
 * npm install -g newman
 * 
 * Usage:
 * newman run Smart_Parking_API.postman_collection.json \
 *   -e Smart_Parking_Local.postman_environment.json \
 *   --reporters cli,json \
 *   --reporter-json-export results.json
 */

const newman = require('newman');

const runOptions = {
    collection: './Smart_Parking_API.postman_collection.json',
    environment: './Smart_Parking_Local.postman_environment.json',
    reporters: ['cli', 'json', 'htmlextra'],
    reporter: {
        htmlextra: {
            export: './test-results.html',
            template: './template.hbs',
            logs: true,
            showOnlyFails: false,
            noSyntaxHighlighting: false,
            testPaging: false,
            browserTitle: "Smart Parking API Test Results",
            title: "Smart Parking Management System API Tests",
            titleSize: 4,
            omitHeaders: false,
            skipHeaders: "User-Agent",
            omitRequestBodies: false,
            omitResponseBodies: false,
            hideRequestBody: [],
            hideResponseBody: [],
            showEnvironmentData: true,
            skipEnvironmentVars: [],
            skipGlobalVars: [],
            skipSensitiveData: true,
            showMarkdownLinks: true,
            showFolderDescription: true,
            timezone: "America/New_York"
        },
        json: {
            export: './test-results.json'
        }
    },
    insecure: true, // Allow self-signed certificates
    timeout: 30000,  // 30 seconds timeout
    timeoutRequest: 10000,  // 10 seconds per request
    delayRequest: 100, // 100ms delay between requests
    iterationData: [], // CSV data file if needed
    globalVar: [], // Global variables
    envVar: [
        { key: 'base_url', value: 'http://localhost:8000' }
    ]
};

// Test scenarios configuration
const testScenarios = {
    smoke: {
        folder: ['Health Check', 'Authentication'],
        description: 'Quick smoke tests to verify basic functionality'
    },
    auth: {
        folder: ['Authentication'],
        description: 'Authentication and authorization tests'
    },
    users: {
        folder: ['User Management'],
        description: 'User management functionality tests'
    },
    parking: {
        folder: ['Parking Management'],
        description: 'Parking lot and availability tests'
    },
    bookings: {
        folder: ['Booking Management'],
        description: 'Booking lifecycle tests'
    },
    admin: {
        folder: ['Administration'],
        description: 'Administrative functionality tests'
    },
    full: {
        description: 'Complete test suite - all endpoints'
    }
};

/**
 * Run a specific test scenario
 * @param {string} scenario - The scenario name (smoke, auth, users, etc.)
 */
function runScenario(scenario = 'smoke') {
    const config = testScenarios[scenario];
    
    if (!config) {
        console.error(`Unknown scenario: ${scenario}`);
        console.log('Available scenarios:', Object.keys(testScenarios).join(', '));
        return;
    }

    const options = { ...runOptions };
    
    if (config.folder) {
        options.folder = config.folder;
    }

    console.log(`\n🚀 Running ${scenario} tests: ${config.description}\n`);

    newman.run(options, (err, summary) => {
        if (err) {
            console.error('❌ Test run failed:', err);
            process.exit(1);
        }

        console.log('\n📊 Test Summary:');
        console.log(`Total Requests: ${summary.run.stats.requests.total}`);
        console.log(`Requests Failed: ${summary.run.stats.requests.failed}`);
        console.log(`Test Scripts Total: ${summary.run.stats.tests.total}`);
        console.log(`Test Scripts Failed: ${summary.run.stats.tests.failed}`);
        console.log(`Assertions Total: ${summary.run.stats.assertions.total}`);
        console.log(`Assertions Failed: ${summary.run.stats.assertions.failed}`);

        if (summary.run.failures.length > 0) {
            console.log('\n❌ Failures:');
            summary.run.failures.forEach((failure, index) => {
                console.log(`${index + 1}. ${failure.error.name}: ${failure.error.message}`);
                if (failure.error.test) {
                    console.log(`   Test: ${failure.error.test}`);
                }
                if (failure.source) {
                    console.log(`   Source: ${failure.source.name || 'Unknown'}`);
                }
            });
            process.exit(1);
        } else {
            console.log('\n✅ All tests passed!');
        }
    });
}

/**
 * Validate collection structure
 */
function validateCollection() {
    const fs = require('fs');
    
    try {
        const collection = JSON.parse(fs.readFileSync('./Smart_Parking_API.postman_collection.json', 'utf8'));
        const environment = JSON.parse(fs.readFileSync('./Smart_Parking_Local.postman_environment.json', 'utf8'));
        
        console.log('✅ Collection file is valid JSON');
        console.log('✅ Environment file is valid JSON');
        console.log(`📁 Collection contains ${collection.item.length} main folders`);
        
        let totalRequests = 0;
        collection.item.forEach(folder => {
            if (folder.item) {
                folder.item.forEach(item => {
                    if (item.request) {
                        totalRequests++;
                    } else if (item.item) {
                        totalRequests += item.item.filter(subItem => subItem.request).length;
                    }
                });
            }
        });
        
        console.log(`🔗 Total API endpoints: ${totalRequests}`);
        console.log(`🌍 Environment variables: ${environment.values.length}`);
        
    } catch (error) {
        console.error('❌ Collection validation failed:', error.message);
        process.exit(1);
    }
}

// Command line interface
const args = process.argv.slice(2);
const command = args[0] || 'smoke';

if (command === 'validate') {
    validateCollection();
} else if (command === 'help') {
    console.log(`
Smart Parking API Test Runner

Usage: node test-runner.js [scenario]

Available scenarios:
${Object.entries(testScenarios).map(([key, config]) => 
    `  ${key.padEnd(10)} - ${config.description}`
).join('\n')}

Commands:
  validate     - Validate collection and environment files
  help         - Show this help message

Examples:
  node test-runner.js smoke      # Run smoke tests
  node test-runner.js full       # Run all tests
  node test-runner.js validate   # Validate files
    `);
} else {
    runScenario(command);
}

module.exports = {
    runScenario,
    validateCollection,
    testScenarios
};
