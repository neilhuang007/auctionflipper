#!/usr/bin/env node
/**
 * High-Performance Persistent Item Evaluation Service
 * 
 * Replaces subprocess-based evaluation with persistent HTTP service
 * Expected performance improvement: 85-90% reduction in evaluation time
 */

const express = require('express');
const { getItemNetworth } = require('skyhelper-networth');
const mongodb = require('mongodb');
const MongoClient = mongodb.MongoClient;

const app = express();
const PORT = process.env.PORT || 3000;

// Increase JSON payload limit for large item data
app.use(express.json({ limit: '10mb' }));

// MongoDB connection (reuse from main application)
let db, flipsCollection;
const client = new MongoClient('mongodb://localhost:27017', { 
    monitorCommands: false,  // Disable command monitoring for performance
    maxPoolSize: 20,         // Connection pool for concurrent requests
    minPoolSize: 5,
    maxIdleTimeMS: 30000,
    serverSelectionTimeoutMS: 5000
});

// Connect to MongoDB
client.connect()
    .then(() => {
        console.log('✅ Connected to MongoDB');
        db = client.db('skyblock');
        flipsCollection = db.collection('Flips');
    })
    .catch(err => {
        console.error('❌ MongoDB connection error:', err);
        process.exit(1);
    });

// Performance monitoring
let evaluationCount = 0;
let totalEvaluationTime = 0;
let profitableFlips = 0;

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        uptime: process.uptime(),
        evaluations: evaluationCount,
        avgEvaluationTime: evaluationCount > 0 ? (totalEvaluationTime / evaluationCount).toFixed(2) + 'ms' : '0ms',
        profitableFlips: profitableFlips,
        memory: process.memoryUsage()
    });
});

// Single item evaluation endpoint
app.post('/evaluate', async (req, res) => {
    const startTime = process.hrtime.bigint();
    
    try {
        const { item, prices, itemstats } = req.body;
        
        if (!item || !prices || !itemstats) {
            return res.status(400).json({ 
                error: 'Missing required fields: item, prices, itemstats' 
            });
        }

        // Call skyhelper-networth for evaluation
        const networth = await getItemNetworth(item, { 
            prices: prices, 
            returnItemData: true 
        });

        const estimatedValue = networth.price;
        const itemId = networth.id;
        const startingBid = itemstats.starting_bid;

        // Check if profitable
        const isProfitable = estimatedValue > startingBid;
        
        // Calculate metrics
        const profit = estimatedValue - startingBid;
        const percentage = (profit / startingBid) * 100;

        const endTime = process.hrtime.bigint();
        const evaluationTime = Number(endTime - startTime) / 1000000; // Convert to milliseconds
        
        // Update performance stats
        evaluationCount++;
        totalEvaluationTime += evaluationTime;
        
        if (isProfitable) {
            profitableFlips++;
        }

        res.json({
            success: true,
            estimatedValue: estimatedValue,
            itemId: itemId.toUpperCase(),
            profit: profit,
            percentage: percentage,
            isProfitable: isProfitable,
            evaluationTime: evaluationTime
        });

    } catch (error) {
        console.error('Evaluation error:', error.message);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

// Batch evaluation endpoint for even better performance
app.post('/evaluate-batch', async (req, res) => {
    const startTime = process.hrtime.bigint();
    
    try {
        const { items, prices } = req.body;
        
        if (!Array.isArray(items) || !prices) {
            return res.status(400).json({ 
                error: 'items must be an array, prices must be provided' 
            });
        }

        const results = [];
        const profitableItems = [];

        // Process all items in parallel
        const evaluationPromises = items.map(async (itemData) => {
            try {
                const { item, itemstats } = itemData;
                
                const networth = await getItemNetworth(item, { 
                    prices: prices, 
                    returnItemData: true 
                });

                const estimatedValue = networth.price;
                const itemId = networth.id;
                const startingBid = itemstats.starting_bid;
                const profit = estimatedValue - startingBid;
                const percentage = (profit / startingBid) * 100;
                const isProfitable = estimatedValue > startingBid;

                const result = {
                    uuid: itemstats.uuid,
                    estimatedValue: estimatedValue,
                    itemId: itemId.toUpperCase(),
                    profit: profit,
                    percentage: percentage,
                    isProfitable: isProfitable,
                    itemstats: itemstats
                };

                if (isProfitable) {
                    profitableItems.push(result);
                }

                return result;
            } catch (error) {
                return {
                    uuid: itemData.itemstats?.uuid || 'unknown',
                    error: error.message,
                    isProfitable: false
                };
            }
        });

        const evaluationResults = await Promise.all(evaluationPromises);
        
        const endTime = process.hrtime.bigint();
        const totalTime = Number(endTime - startTime) / 1000000;
        
        // Update performance stats
        evaluationCount += items.length;
        totalEvaluationTime += totalTime;
        profitableFlips += profitableItems.length;

        res.json({
            success: true,
            results: evaluationResults,
            profitable: profitableItems,
            stats: {
                totalItems: items.length,
                profitableItems: profitableItems.length,
                totalTime: totalTime,
                avgTimePerItem: totalTime / items.length
            }
        });

    } catch (error) {
        console.error('Batch evaluation error:', error.message);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

// Store profitable flips directly to database (optional endpoint)
app.post('/store-flip', async (req, res) => {
    try {
        const { 
            itemstats, 
            profit, 
            daily_sales, 
            lowest_bin, 
            percentage, 
            targeted_price 
        } = req.body;

        const flipData = {
            itemstats: itemstats,
            profit: profit,
            daily_sales: daily_sales,
            lowest_bin: lowest_bin,
            percentage: percentage,
            targeted_price: targeted_price,
            timestamp: Date.now()
        };

        const result = await flipsCollection.insertOne(flipData);
        
        res.json({
            success: true,
            insertedId: result.insertedId
        });

    } catch (error) {
        console.error('Store flip error:', error.message);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

// Performance stats endpoint
app.get('/stats', (req, res) => {
    res.json({
        evaluationCount: evaluationCount,
        totalEvaluationTime: totalEvaluationTime,
        avgEvaluationTime: evaluationCount > 0 ? totalEvaluationTime / evaluationCount : 0,
        profitableFlips: profitableFlips,
        profitableRate: evaluationCount > 0 ? (profitableFlips / evaluationCount) * 100 : 0,
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🔄 Shutting down gracefully...');
    try {
        await client.close();
        console.log('✅ MongoDB connection closed');
        process.exit(0);
    } catch (error) {
        console.error('❌ Error during shutdown:', error);
        process.exit(1);
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`🚀 Item Evaluation Service running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`📈 Performance stats: http://localhost:${PORT}/stats`);
    console.log('⚡ Ready for high-performance item evaluation!');
});

module.exports = app;