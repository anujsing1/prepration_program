/**
 * 
 */
package com.study;

import java.util.HashMap;
import java.util.Map;

/**
 * @author govind.gupta
 *
 */
public class PersistentTest_Q3 {
	
	private Map<String, String> m = new HashMap<String, String>();
	
	/*public PersistentTest_Q3(){
		m.put("Mickey", "Mouse");
		m.put("Mickey", "Mantel");
	}*/
	
	public void PersistentTest(){
		m.put("Mickey", "Mouse");
		m.put("Mickey", "Mantel");
	}
	
	public int size(){
		return m.size();
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		PersistentTest_Q3 test = new PersistentTest_Q3();
		System.out.println(test.size());
	}

}
