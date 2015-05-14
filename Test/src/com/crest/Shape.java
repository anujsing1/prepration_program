package com.crest;

public class Shape {
	private Character cmd;
	private int x1;
	private int y1;
	private int x2;
	private int y2;
	
	private String Description;
	
	/**
	 * @param cmd
	 * @param x
	 * @param y
	 */
	public Shape(Character cmd, int x, int y) {
		this.cmd = cmd;
		this.x1 = x;
		this.y1 = y;
		this.Description = "Fill Color";
	}
	
	/**
	 * @param cmd
	 * @param x1
	 * @param y1
	 * @param x2
	 * @param y2
	 */
	public Shape(Character cmd, int x1, int y1, int x2, int y2) {
		this.cmd = cmd;
		this.x1 = x1;
		this.y1 = y1;
		this.x2 = x2;
		this.y2 = y2;
		if (cmd == 'R')
			this.Description = "Rectangel";
		else
			this.Description = "Line";
	}

	/**
	 * @return the cmd
	 */
	public Character getCmd() {
		return cmd;
	}

	/**
	 * @param cmd the cmd to set
	 */
	public void setCmd(Character cmd) {
		this.cmd = cmd;
	}

	/**
	 * @return the x1
	 */
	public int getX1() {
		return x1;
	}

	/**
	 * @param x1 the x1 to set
	 */
	public void setX1(int x1) {
		this.x1 = x1;
	}

	/**
	 * @return the y1
	 */
	public int getY1() {
		return y1;
	}

	/**
	 * @param y1 the y1 to set
	 */
	public void setY1(int y1) {
		this.y1 = y1;
	}

	/**
	 * @return the x2
	 */
	public int getX2() {
		return x2;
	}

	/**
	 * @param x2 the x2 to set
	 */
	public void setX2(int x2) {
		this.x2 = x2;
	}

	/**
	 * @return the y2
	 */
	public int getY2() {
		return y2;
	}

	/**
	 * @param y2 the y2 to set
	 */
	public void setY2(int y2) {
		this.y2 = y2;
	}

	/**
	 * @return the description
	 */
	public String getDescription() {
		return Description;
	}

	/**
	 * @param description the description to set
	 */
	public void setDescription(String description) {
		Description = description;
	}
}
