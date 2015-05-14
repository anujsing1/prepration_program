package com.groupon;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class StringSink extends Sink<String>{
	final List<String> list = new ArrayList<String>();
	void add(String... elements){
		list.addAll(Arrays.asList(elements));
	}
	
	@Override
	public String toString() {
		return list.toString();
	}
	
	public static void main(String[] args) {
		Sink<String> ss = new StringSink();
		ss.addUnlessNull("null", null);
		System.out.println(ss);
	}
}
