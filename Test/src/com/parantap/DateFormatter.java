/**
 * 
 */
package com.parantap;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * @author govind.gupta
 *
 */
public class DateFormatter {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		String str = "20th Oct 2052";
		SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd");
		Date d = new Date("str");
		format.format(d);
		System.out.println(d.getDate());
	}

}
