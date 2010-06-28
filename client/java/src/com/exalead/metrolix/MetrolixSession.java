package com.exalead.metrolix;

import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.management.ManagementFactory;
import java.net.HttpURLConnection;
import java.net.URL;

public class MetrolixSession {
    String sessionToken;

    public void reportResult(String path, double value) {
        if (sessionToken == null) return;

        try {
            String content = "{\"session_token\":\"" + sessionToken + "\",\"path\":\"" + path + "\",\"value\":\"" + value + "\"}";
            URL target = new URL(MetrolixClient.server + "/server/report_result");
            HttpURLConnection connection = (HttpURLConnection) target.openConnection();
            connection.setDoOutput(true);
            Writer wr = new OutputStreamWriter(connection.getOutputStream());
            wr.write(content);
            wr.flush();
            int code = connection.getResponseCode();
            if (code != 200) {
                System.out.println("Failed to report to Metrolix, bad return code:" + code);
            }
        } catch (Exception e) {
            System.out.println("Failed to report to Metrolix, exception: " + e);
        }
    }
    
    public void startStopWatch() {
        startStopWatch(false);
    }
    
    public void startStopWatch(boolean cpuTime) {
        startSW = System.currentTimeMillis();
        if (cpuTime) {
            startSWCPU = ManagementFactory.getThreadMXBean().getCurrentThreadCpuTime();
            startSWUserCPU = ManagementFactory.getThreadMXBean().getCurrentThreadUserTime();
        }
    }
    long startSW;
    long startSWCPU, startSWUserCPU;
    
    public void stopStopWatch(String pathToReport) {
        stopStopWatch(pathToReport, false);
    }
    
    public void stopStopWatch(String pathToReport, boolean cpuTime) {
        long stopSW = System.currentTimeMillis();
        reportResult(pathToReport, stopSW - startSW);
        if (cpuTime) {
            long stopSWCPU = ManagementFactory.getThreadMXBean().getCurrentThreadCpuTime();
            long stopSWUserCPU = ManagementFactory.getThreadMXBean().getCurrentThreadUserTime();
            long totalSystem = (stopSWCPU - startSWCPU) - (stopSWUserCPU - startSWUserCPU);
            reportResult(pathToReport + "/cputime", (stopSWCPU - startSWCPU)/1000000);
            reportResult(pathToReport + "/ucputime", (stopSWUserCPU - startSWUserCPU)/1000000);
            reportResult(pathToReport + "/scputime", totalSystem/1000000);
        }
        startSW = 0;
        startSWCPU = 0;
        startSWUserCPU = 0;
    }
}
