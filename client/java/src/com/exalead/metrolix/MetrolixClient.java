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
     * If parameters are not set and not given in the createSession call, the
     * METROLIX_SERVER, METROLIX_PROJECT, METROLIX_PROJECT_BRANCH, METROLIX_PROJECT_VERSION,
     * METROLIX_SESSION_NAME and METROLIX_SESSION_TESTSET
     * environment variables are used
     */
    public static void setParams(String server, String project, String projectBranch, String projectVersion,
            String sessionName, String sessionTestset) {
        MetrolixClient.server = server;
        MetrolixClient.project = project;
        MetrolixClient.projectBranch = projectBranch;
        MetrolixClient.projectVersion = projectVersion;
        MetrolixClient.sessionName = sessionName;
        MetrolixClient.testset = sessionTestset;
    }

    protected static boolean enabled() {
        return server != null || System.getenv("METROLIX_SERVER") != null; 
    }

    /**
     * Get an object to report to the Metrolix server using an already-started
     * session.
     * If newSession() was never used, the session token will be searched in the
     * METROLIX_SESSION environment variable
     */
    public synchronized static MetrolixSession retrieveSession() {
        if (!enabled()) {
            System.out.println("Metrolix server disabled");
            return new MetrolixSession();
        }
        if (savedSession != null) {
            return savedSession;
        }
        MetrolixSession ps = new MetrolixSession();
        if (!enabled) {
            return ps;
        }
        if (savedSessionToken == null) {
            savedSessionToken = System.getenv("METROLIX_SESSION");
        }
        ps.sessionToken = savedSessionToken;
        savedSession = ps;
        return ps;
    }
    
    public synchronized static MetrolixSession newSession() {
        return newSession(null, null, null, null, null, null);
    }

    public synchronized static MetrolixSession newSession(String server, String project,
            String projectBranch, String projectVersion, String sessionName, String sessionTestset) {
        if (!enabled()) return new MetrolixSession();
        return newSessionResolved(
                server != null ? server : (MetrolixClient.server != null ? MetrolixClient.server : System.getenv("METROLIX_SERVER")),
                        project != null ? project : (MetrolixClient.project != null ? MetrolixClient.project : System.getenv("METROLIX_PROJECT")),
                                projectBranch != null ? projectBranch : (MetrolixClient.projectBranch != null ? MetrolixClient.projectBranch : System.getenv("METROLIX_PROJECT_BRANCH")),
                                        projectVersion != null ? projectVersion : (MetrolixClient.projectVersion != null ? MetrolixClient.projectVersion : System.getenv("METROLIX_PROJECT_VERSION")),
                                                sessionName != null ? sessionName : (MetrolixClient.sessionName != null ? MetrolixClient.sessionName: System.getenv("METROLIX_SESSION_NAME")),
                                                        sessionTestset != null ? sessionTestset : (MetrolixClient.testset != null ? MetrolixClient.testset: System.getenv("METROLIX_SESSION_TESTSET")));
    }

    private static String jsonEscape(String x) {
        return x.replace("\"", "\\\"");
    }

    private synchronized static MetrolixSession newSessionResolved(String server, String project,
            String projectBranch, String projectVersion, String sessionName, String sessionTestset) {

        if (server == null) throw new IllegalArgumentException("Could not find metrolix server");
        if (project== null) throw new IllegalArgumentException("Could not find metrolix project");
        
        MetrolixSession ps = new MetrolixSession();

        try {
            String content = "{" +
                    "\"project_name\":\"" + jsonEscape(project) + "\"," +
                    (projectVersion != null ? "\"version\":\"" + jsonEscape(projectVersion) + "\","  : "")+ 
                    (projectBranch != null ? "\"branch\":\"" + jsonEscape(projectBranch) + "\","  : "" )+ 
                    (sessionName != null ? "\"session_name\":\"" + jsonEscape(sessionName) + "\","  : "") + 
                    (sessionTestset != null ? "\"testset\":\"" + jsonEscape(sessionTestset) + "\""  : "") + 
                    "}";
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
    static String projectBranch;
    static String projectVersion;
    static String testset;
    static String sessionName;

    static String savedSessionToken;
    static MetrolixSession savedSession;
    static boolean enabled = true;
}
