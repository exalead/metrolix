package com.exalead.metrolix;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.HttpURLConnection;
import java.net.URL;

public class MetrolixClient {
    /**
     * Set parameters to report to metrolix server.
     * If parameters are not set, the METROLIX_SERVER and METROLIX_PROJECT
     * environment variables are used
     */
    public static void setParams(String _server, String _project) {
        server = _server;
        project = _project;
    }
    
    /**
     * Get an object to report to the Metrolix server using an already-started
     * session.
     * If newSession() was never used, the session token will be searched in the
     * METROLIX_SESSION environment variable
     */
    public synchronized static MetrolixSession retrieveSession() {
        if (savedSession != null) {
            return savedSession;
        }
        if (server == null || project == null) {
            server = System.getenv("METROLIX_SERVER");
            project = System.getenv("METROLIX_PROJECT");
        }
        if (server == null || project == null) {
            enabled = false;
        }
        
        MetrolixSession ps = new MetrolixSession();
        if (!enabled) {
            System.out.println("Metrolix server disabled");
            return ps;
        }
        if (savedSessionToken == null) {
            savedSessionToken = System.getenv("METROLIX_SESSION");
        }
        ps.sessionToken = savedSessionToken;
        savedSession = ps;
        return ps;
    }
    
    /**
     * Create a new reporting session on the Metrolix server.
     * The session can be reused by calling retrieveSession()
     */
    public synchronized static MetrolixSession newSession() {
        if (server == null || project == null) {
            server = System.getenv("METROLIX_SERVER");
            project = System.getenv("METROLIX_PROJECT");
        }
        if (server == null || project == null) {
            enabled = false;
        }
        
        MetrolixSession ps = new MetrolixSession();
        if (!enabled) {
            System.out.println("Metrolix server disabled");
            return ps;
        }

        try {
            String content = "{\"project_name\":\"" + project + "\"}";
            URL target = new URL(server  + "/server/start_session");
            HttpURLConnection connection = (HttpURLConnection) target.openConnection();
            connection.setDoOutput(true);
            Writer wr = new OutputStreamWriter(connection.getOutputStream());
            wr.write(content);
            wr.flush();
            int code = connection.getResponseCode();
            if (code != 200) {
                throw new Exception("Bad return code:" + code);
            }
            BufferedReader rd = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            String token = rd.readLine();
            ps.sessionToken = token;
            savedSessionToken = ps.sessionToken;
        } catch (Throwable t) {
            System.out.println("Disabling Metrolix because of exception: " +  t);
        }
        savedSession = ps;

        return ps;
    }

    static String server;
    static String project;
    static String savedSessionToken;
    static MetrolixSession savedSession;
    static boolean enabled = true;
}
